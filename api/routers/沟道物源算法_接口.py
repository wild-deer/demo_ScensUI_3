
from fastapi import APIRouter, UploadFile, File, Request
from pathlib import Path
import os
import sys
import uuid
import shutil
import zipfile
import re
import importlib
import importlib.util

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

base_dir = Path(root_dir)
outputs_dir = base_dir / "outputs"
outputs_dir.mkdir(exist_ok=True)

# 导入封装后的算法模块
# 注意：模块名包含中文括号，建议使用 importlib 动态导入
SUBMOD_DIR = base_dir / "submod"
sys.path.append(str(SUBMOD_DIR))

# 尝试导入模块
try:
    # 模块名为 "沟道物源（完美）"
    algo_module_name = "沟道物源（完美）"
    if algo_module_name not in sys.modules:
        algo_spec = importlib.util.spec_from_file_location(algo_module_name, SUBMOD_DIR / f"{algo_module_name}.py")
        algo_module = importlib.util.module_from_spec(algo_spec)
        sys.modules[algo_module_name] = algo_module
        algo_spec.loader.exec_module(algo_module)
    else:
        algo_module = sys.modules[algo_module_name]
except Exception as e:
    print(f"Failed to import algorithm module: {e}")
    algo_module = None

@router.post("/channel-source")
async def channel_source_algorithm(
    dem_zip: UploadFile = File(...),
    boundary_kml: UploadFile = File(...),
    profile_kml: UploadFile = File(...),
    request: Request = None
):
    """
    功能
    - 沟道物源算法：调用后端脚本 `submod/沟道物源（完美）.py` 的 `run_algorithm` 函数。
    - 接口路径：`POST /channel-source`
    - 请求类型：`multipart/form-data`
    """
    if not algo_module:
        return {"error": "Algorithm module not loaded"}

    uid = uuid.uuid4().hex
    task_dir = outputs_dir / f"{uid}_channel_source"
    task_dir.mkdir(exist_ok=True)

    # 1. 准备输入文件
    # 1.1 DEM
    dem_zip_name = f"{uid}_{Path(dem_zip.filename).name}"
    dem_zip_path = task_dir / dem_zip_name
    with dem_zip_path.open("wb") as f:
        dem_zip.file.seek(0)
        shutil.copyfileobj(dem_zip.file, f)
    
    dem_extract_dir = task_dir / "dem_extracted"
    dem_extract_dir.mkdir(exist_ok=True)
    
    dem_path = None
    if zipfile.is_zipfile(str(dem_zip_path)):
        try:
            with zipfile.ZipFile(str(dem_zip_path), 'r') as zf:
                for info in zf.infolist():
                    name = info.filename
                    # 解决中文编码
                    try:
                        name = name.encode('cp437').decode('gbk')
                    except:
                        try:
                            name = name.encode('cp437').decode('utf-8')
                        except:
                            pass
                    
                    target_path = dem_extract_dir / name
                    if info.is_dir() or name.endswith("/"):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, target_path.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
        except Exception:
            return {"error": "bad_zip_file"}
            
        tif_candidates = list(dem_extract_dir.rglob("*.tif")) + list(dem_extract_dir.rglob("*.tiff"))
        # 过滤掉 aux.xml 等非数据文件
        tif_candidates = [p for p in tif_candidates if "aux" not in p.name.lower()]
        if tif_candidates:
            # 简单策略：取最大的文件，通常是 DEM 数据
            tif_candidates.sort(key=lambda x: x.stat().st_size, reverse=True)
            dem_path = tif_candidates[0]
    
    if not dem_path:
        return {"error": "no_tif_found_in_zip"}

    # 1.2 Boundary KML
    boundary_kml_path = task_dir / f"boundary_{uid}.kml"
    with boundary_kml_path.open("wb") as f:
        boundary_kml.file.seek(0)
        shutil.copyfileobj(boundary_kml.file, f)

    # 1.3 Profile KML
    profile_kml_path = task_dir / f"profile_{uid}.kml"
    with profile_kml_path.open("wb") as f:
        profile_kml.file.seek(0)
        shutil.copyfileobj(profile_kml.file, f)

    # 2. 调用算法
    # 注入/Mock plt.show 以避免阻塞并保存图片
    # 注意：由于我们是在同一个进程中运行，直接修改 algo_module.plt.show 是危险的，因为它会影响全局
    # 但考虑到这是一个 Demo/单任务场景，或者我们可以用 matplotlib 的非交互后端
    import matplotlib
    matplotlib.use('Agg') # 使用非交互式后端
    import matplotlib.pyplot as plt
    
    # 定义一个保存图片的函数
    def save_figure_hook(*args, **kwargs):
        # 保存当前 figure
        try:
            filename = f"figure_{uuid.uuid4().hex[:6]}.png"
            plt.savefig(task_dir / filename)
            plt.close()
        except Exception as e:
            print(f"Error saving figure: {e}")

    # 临时替换 plt.show
    original_show = plt.show
    plt.show = save_figure_hook

    # 捕获 stdout/stderr
    from io import StringIO
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = my_stdout = StringIO()
    sys.stderr = my_stderr = StringIO()

    try:
        # 调用封装的函数
        # 注意：run_algorithm 会切换 CWD 到 task_dir，这是线程不安全的
        # 如果是多线程环境，这会有问题。但在 FastAPI 的 async def 中（通常运行在主线程或线程池），
        # os.chdir 会影响整个进程。这是一个潜在风险点。
        # 更好的做法是修改 run_algorithm 不依赖 os.chdir，而是传递 output_dir。
        # 但目前为了最小化修改，我们加个锁或者只能这样。
        
        # 传入绝对路径
        algo_module.run_algorithm(
            dem_path=str(dem_path.absolute()),
            boundary_kml=str(boundary_kml_path.absolute()),
            profile_kml=str(profile_kml_path.absolute()),
            work_dir=str(task_dir.absolute())
        )
        
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return {
            "error": "Algorithm execution failed",
            "message": str(e),
            "logs": {
                "stdout": my_stdout.getvalue(),
                "stderr": my_stderr.getvalue() + f"\nException: {traceback.format_exc()}"
            }
        }
    finally:
        # 恢复环境
        plt.show = original_show
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        # 切回原来的目录 (虽然 run_algorithm 内部已经切回去了，但为了保险)
        os.chdir(current_dir)

    # 3. 收集结果
    expected_files = {
        "x123_csv": "每组X1_X2_X3坐标点.csv",
        "bspline_csv": "B样条点坐标.csv",
        "boundary_csv": "DEM边界点坐标.csv",
        "merged_csv": "拟合点坐标.csv",
        "generated_dem": "output_dem.tif",
        "final_clipped_dem": "final_clip_test.tif",
    }

    result_urls = {}
    base_url = str(request.base_url).rstrip("/")
    
    def get_url(filename):
        fpath = task_dir / filename
        if fpath.exists():
            rel_path = fpath.relative_to(outputs_dir)
            return f"{base_url}/files/{rel_path.as_posix()}"
        return None

    for key, filename in expected_files.items():
        url = get_url(filename)
        if url:
            result_urls[key] = url

    # 查找生成的图片
    images = list(task_dir.glob("figure_*.png"))
    image_urls = [get_url(img.name) for img in images]
    
    # 解析体积结果 (从 stdout)
    stdout_content = my_stdout.getvalue()
    volume = None
    if stdout_content:
        match = re.search(r"修正后体积计算结果:\s*([-\d.]+)\s*立方米", stdout_content)
        if match:
            volume = float(match.group(1))

    return {
        "id": uid,
        "volume": volume,
        "visualization_urls": image_urls,
        "files": result_urls,
        "logs": {
            "stdout": stdout_content[:5000],
            "stderr": my_stderr.getvalue()[:5000]
        }
    }
