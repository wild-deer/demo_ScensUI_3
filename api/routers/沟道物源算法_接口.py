
from fastapi import APIRouter, UploadFile, File, Request
from pathlib import Path
import os
import sys
import uuid
import shutil
import zipfile
import re
import subprocess

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

base_dir = Path(root_dir)
outputs_dir = base_dir / "outputs"
outputs_dir.mkdir(exist_ok=True)

# 指向原始脚本路径
ORIGINAL_SCRIPT_PATH = base_dir / "submod" / "沟道物源（完美）.py"

@router.post("/channel-source")
async def channel_source_algorithm(
    dem_zip: UploadFile = File(...),
    boundary_kml: UploadFile = File(...),
    profile_kml: UploadFile = File(...),
    request: Request = None
):
    """
    功能
    - 沟道物源算法：直接调用后端脚本 `submod/沟道物源（完美）.py` 进行计算。
    - 接口路径：`POST /channel-source`
    - 请求类型：`multipart/form-data`
    
    原理
    - 动态替换脚本中的硬编码输入路径，并在隔离环境中执行，不修改原脚本文件。
    """
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

    # 2. 读取原始脚本并动态替换
    try:
        with open(ORIGINAL_SCRIPT_PATH, "r", encoding="utf-8") as f:
            script_content = f.read()
    except Exception as e:
        return {"error": f"Failed to read original script: {e}"}

    # 替换规则：
    # 原始DEM = r"..." -> 原始DEM = r"{dem_path}"
    # 剖面线kml = r"..." -> 剖面线kml = r"{profile_kml_path}"
    # 边界kml_path = r"..." -> 边界kml_path = r"{boundary_kml_path}"
    
    # 使用正则替换，确保路径转义安全
    # Python 路径在 Windows 上是反斜杠，但在字符串里最好用正斜杠或双反斜杠
    safe_dem_path = str(dem_path).replace("\\", "/")
    safe_profile_path = str(profile_kml_path).replace("\\", "/")
    safe_boundary_path = str(boundary_kml_path).replace("\\", "/")

    script_content = re.sub(
        r'原始DEM\s*=\s*r?".*?"', 
        f'原始DEM = r"{safe_dem_path}"', 
        script_content, 
        count=1
    )
    script_content = re.sub(
        r'剖面线kml\s*=\s*r?".*?"', 
        f'剖面线kml = r"{safe_profile_path}"', 
        script_content, 
        count=1
    )
    script_content = re.sub(
        r'边界kml_path\s*=\s*r?".*?"', 
        f'边界kml_path = r"{safe_boundary_path}"', 
        script_content, 
        count=1
    )

    # 禁用 plt.show() 以免阻塞
    # 替换为 plt.savefig('visualization_result.png') 或直接 pass
    # 注意：原脚本有多处 plt.show()，我们根据上下文来处理
    # 比如最后的 3D 可视化，我们希望保存下来
    
    # 简单粗暴：把 plt.show() 替换为 pass，但这样就没图了。
    # 更好的方法：在脚本开头加一行：plt.show = lambda: plt.savefig(f"figure_{uuid.uuid4().hex[:4]}.png")
    # 但原脚本导入了 matplotlib.pyplot as plt，所以我们需要在 import 之后注入
    
    injection_code = """
import matplotlib.pyplot as plt
def save_and_close():
    import uuid
    plt.savefig(f"figure_{uuid.uuid4().hex[:4]}.png")
    plt.close()
plt.show = save_and_close
"""
    # 插入到 import 块之后
    # 找到最后一个 import
    last_import_idx = 0
    lines = script_content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import_idx = i
    
    lines.insert(last_import_idx + 1, injection_code)
    modified_script_content = "\n".join(lines)

    # 3. 写入临时执行脚本
    temp_script_path = task_dir / "runner.py"
    with open(temp_script_path, "w", encoding="utf-8") as f:
        f.write(modified_script_content)

    # 4. 执行脚本
    # 注意：必须在 task_dir 下执行，这样生成的相对路径文件才会出现在 task_dir 里
    try:
        # 使用当前 python 环境执行
        env = os.environ.copy()
        # 确保 PYTHONPATH 包含项目根目录，以便能找到 submod 等（虽然这里是单脚本执行，可能不需要）
        env["PYTHONPATH"] = str(root_dir)
        
        # 增加超时机制，防止死循环
        process = subprocess.run(
            [sys.executable, str(temp_script_path)],
            cwd=str(task_dir),
            capture_output=True,
            text=True,
            env=env,
            timeout=300 # 5分钟超时
        )
        
        if process.returncode != 0:
            return {
                "error": "Script execution failed",
                "stderr": process.stderr,
                "stdout": process.stdout
            }
            
    except subprocess.TimeoutExpired:
        return {"error": "Script execution timed out"}
    except Exception as e:
        return {"error": f"Execution error: {str(e)}"}

    # 5. 收集结果
    # 原脚本生成的文件名通常是固定的
    expected_files = {
        "x123_csv": "每组X1_X2_X3坐标点.csv",
        "bspline_csv": "B样条点坐标.csv",
        "boundary_csv": "DEM边界点坐标.csv",
        "merged_csv": "拟合点坐标.csv",
        "generated_dem": "output_dem.tif",
        "final_clipped_dem": "final_clip_test.tif", # 原脚本里 output_path = "final_clip_test.tif"
    }

    result_urls = {}
    base_url = str(request.base_url).rstrip("/")
    
    # 辅助函数生成 URL
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
    # 因为我们替换了 plt.show，图片名是随机的 figure_xxxx.png
    # 或者原脚本可能有显式保存的图片？原脚本没有 savefig，只有 show
    # 但我们注入的代码会保存为 figure_xxxx.png
    images = list(task_dir.glob("figure_*.png"))
    image_urls = [get_url(img.name) for img in images]
    
    # 尝试解析 stdout 获取体积值
    # 原脚本输出：修正后体积计算结果: 12345.67 立方米
    volume = None
    if process.stdout:
        match = re.search(r"修正后体积计算结果:\s*([-\d.]+)\s*立方米", process.stdout)
        if match:
            volume = float(match.group(1))

    return {
        "id": uid,
        "volume": volume,
        "visualization_urls": image_urls,
        "files": result_urls,
        "logs": {
            "stdout": process.stdout[:2000] if process.stdout else "", # 截断日志防止过大
            "stderr": process.stderr[:2000] if process.stderr else ""
        }
    }
