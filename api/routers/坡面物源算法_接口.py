from fastapi import APIRouter, UploadFile, File, Request, Form
from pathlib import Path
import os
import sys
import uuid
import shutil
import zipfile
import importlib
import numpy as np
import json
from typing import List

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

base_dir = Path(root_dir)
outputs_dir = base_dir / "outputs"
outputs_dir.mkdir(exist_ok=True)

@router.post("/c-factor")
async def c_factor(ndvi_file: UploadFile = File(...), shp_zip: UploadFile = File(...), request: Request = None):
    """
    功能
    - 计算植被覆盖度 f 与 C 因子，并输出裁剪后的 NDVI、f、C 以及统计报告与可视化图片。
    - 接口路径：`POST /c-factor`
    - 请求类型：`multipart/form-data`

    输入参数
    - `ndvi_file`：NDVI 栅格文件（通常为单波段 GeoTIFF，字段名为 `ndvi_file`）
      - 用途：作为计算 f 与 C 的基础栅格数据
      - 要求：坐标参考与矢量范围一致或可裁剪；文件类型建议为 `.tif`
    - `shp_zip`：矢量范围压缩包（字段名为 `shp_zip`）
      - 用途：用于裁剪 NDVI；压缩包内需包含 `.shp/.shx/.dbf/.prj` 等文件
      - 编码：自动尝试 `utf-8/gbk/cp936` 解决中文文件名
    - `request`：FastAPI `Request`，用于拼接返回的文件访问 URL

    输出结果（JSON）
    - `id`：本次计算的唯一标识
    - `ndvi_tif_url`：原始 NDVI 栅格的可访问 URL
    - `shp_zip_url`：上传的矢量 ZIP 的可访问 URL
    - `clipped_ndvi_tif_url`：按矢量范围裁剪后的 NDVI 栅格 URL（文件名：`裁剪后ndvi.tif`）
    - `f_tif_url`：植被覆盖度 f 的栅格 URL（文件名：`植被覆盖度f.tif`）
    - `c_tif_url`：C 因子栅格 URL（文件名：`C因子.tif`）
    - `report_url`：统计报告文本 URL（文件名：`statistics_report.txt`）
    - `visualization_url`：分析结果可视化图片 URL（文件名：`vegetation_analysis_results.png`）
    - `c_stats`：C 因子统计（`min/max/mean`，浮点数；忽略 `NaN`）
    - `f_stats`：f 统计（`min/max/mean`，浮点数；忽略 `NaN`）

    错误响应（JSON）
    - `{"error": "not_a_zip_file", "filename": ..., "size": ...}`：`shp_zip` 不是有效 ZIP
    - `{"error": "bad_zip_file", "filename": ..., "size": ...}`：ZIP 文件损坏
    - `{"error": "no_shp_found_in_zip"}`：ZIP 内未找到 `.shp`
    """
    uid = uuid.uuid4().hex
    ndvi_name = f"{uid}_{Path(ndvi_file.filename).stem}.tif"
    ndvi_path = outputs_dir / ndvi_name
    with ndvi_path.open("wb") as f:
        ndvi_file.file.seek(0)
        shutil.copyfileobj(ndvi_file.file, f)

    shpzip_name = f"{uid}_{Path(shp_zip.filename).name}"
    shpzip_path = outputs_dir / shpzip_name
    with shpzip_path.open("wb") as f:
        shp_zip.file.seek(0)
        shutil.copyfileobj(shp_zip.file, f)

    shp_extract_dir = outputs_dir / f"{uid}_shp"
    shp_extract_dir.mkdir(exist_ok=True)
    if not zipfile.is_zipfile(str(shpzip_path)):
        return {"error": "not_a_zip_file", "filename": shpzip_name, "size": os.path.getsize(shpzip_path)}
    try:
        with zipfile.ZipFile(str(shpzip_path), 'r') as zf:
            for info in zf.infolist():
                name = info.filename
                fixed = name
                if not (info.flag_bits & 0x800):
                    for enc in ("utf-8", "gbk", "cp936"):
                        try:
                            fixed = name.encode("cp437").decode(enc)
                            break
                        except Exception:
                            pass
                target_path = shp_extract_dir / fixed
                if info.is_dir() or name.endswith("/"):
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, target_path.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile:
        return {"error": "bad_zip_file", "filename": shpzip_name, "size": os.path.getsize(shpzip_path)}

    shp_candidates = list(shp_extract_dir.rglob("*.shp"))
    if not shp_candidates:
        return {"error": "no_shp_found_in_zip"}
    shp_path = shp_candidates[0]

    algo = importlib.import_module("submod.坡面物源算法.C因子")
    out_dir = outputs_dir / f"{uid}_c_factor"
    out_dir.mkdir(exist_ok=True)
    C, f = algo.calculate_vegetation_cover_factor(str(ndvi_path), str(shp_path), output_dir=str(out_dir))

    c_stats = None
    f_stats = None
    if C is not None and f is not None:
        c_stats = {
            "min": float(np.nanmin(C)),
            "max": float(np.nanmax(C)),
            "mean": float(np.nanmean(C))
        }
        f_stats = {
            "min": float(np.nanmin(f)),
            "max": float(np.nanmax(f)),
            "mean": float(np.nanmean(f))
        }

    base = str(request.base_url).rstrip("/")
    def url_of(name): return f"{base}/files/{uid}_c_factor/{name}"
    clipped_ndvi_url = url_of("裁剪后ndvi.tif")
    f_tif_url = url_of("植被覆盖度f.tif")
    c_tif_url = url_of("C因子.tif")
    report_url = url_of("statistics_report.txt")
    vis_url = url_of("vegetation_analysis_results.png")

    return {
        "id": uid,
        "ndvi_tif_url": f"{base}/files/{ndvi_name}",
        "shp_zip_url": f"{base}/files/{shpzip_name}",
        "clipped_ndvi_tif_url": clipped_ndvi_url,
        "f_tif_url": f_tif_url,
        "c_tif_url": c_tif_url,
        "report_url": report_url,
        "visualization_url": vis_url,
        "c_stats": c_stats,
        "f_stats": f_stats
    }

@router.post("/k-factor")
async def k_factor(raster_file: UploadFile = File(...), shp_zip: UploadFile = File(...), attribute_xls: UploadFile = File(...), request: Request = None):
    """
    功能
    - 计算 K 因子，并生成：裁剪栅格、带属性的栅格/表、K 因子栅格与统计。
    - 接口路径：`POST /k-factor`
    - 请求类型：`multipart/form-data`

    输入参数
    - `raster_file`：待计算的栅格或压缩包（字段名为 `raster_file`）
      - 用途：作为裁剪与后续属性计算的基础数据
      - 支持：直接栅格文件（如 `.tif`）；或 ZIP 压缩包（例如 HWSD 数据集，包含 `hwsd.bil/.hdr/.prj` 等），会自动解压并优先选择 `.bil` 作为输入
    - `shp_zip`：矢量范围压缩包（字段名为 `shp_zip`）
      - 用途：用于裁剪栅格；压缩包内需包含 `.shp/.shx/.dbf/.prj` 等文件
      - 编码：自动尝试 `utf-8/gbk/cp936` 解决中文文件名
    - `attribute_xls`：属性表（Excel，字段名为 `attribute_xls`）
      - 用途：为裁剪后的栅格构建属性表并参与 K 因子计算
      - 建议：`.xls` 或 `.xlsx`
    - `request`：FastAPI `Request`，用于拼接返回的文件访问 URL

    输出结果（JSON）
    - `id`：本次计算的唯一标识
    - `raster_url`：上传原始栅格的可访问 URL
    - `shp_zip_url`：上传矢量 ZIP 的可访问 URL
    - `attribute_xls_url`：上传属性 Excel 的可访问 URL
    - `clipped_tif_url`：按矢量范围裁剪后的栅格 URL（文件名：`clipped.tif`）
    - `attribute_tif_url`：包含属性的栅格 URL（文件名：`clipped_with_attributes.tif`）
    - `attribute_csv_url`：由属性表生成的 CSV URL
    - `k_tif_url`：K 因子栅格 URL（文件名：`k因子.tif`）
    - `k_values_csv_url`：K 因子值的统计表 CSV URL
    - `k_stats`：K 因子统计（`min/max/mean`，已将 `nodata` 与 `-9999` 视为缺失并忽略）

    错误响应（JSON）
    - `{"error": "not_a_zip_file", "filename": ..., "size": ...}`：`shp_zip` 不是有效 ZIP
    - `{"error": "bad_zip_file", "filename": ..., "size": ...}`：ZIP 文件损坏
    - `{"error": "no_shp_found_in_zip"}`：ZIP 内未找到 `.shp`
    """
    uid = uuid.uuid4().hex
    out_dir = outputs_dir / f"{uid}_k_factor"
    out_dir.mkdir(exist_ok=True)
    raster_name = f"{uid}_{Path(raster_file.filename).name}"
    raster_path = out_dir / raster_name
    with raster_path.open("wb") as f:
        raster_file.file.seek(0)
        shutil.copyfileobj(raster_file.file, f)
    shpzip_name = f"{uid}_{Path(shp_zip.filename).name}"
    shpzip_path = out_dir / shpzip_name
    with shpzip_path.open("wb") as f:
        shp_zip.file.seek(0)
        shutil.copyfileobj(shp_zip.file, f)
    xls_ext = Path(attribute_xls.filename).suffix or ".xls"
    xls_name = f"{uid}_{Path(attribute_xls.filename).stem}{xls_ext}"
    xls_path = out_dir / xls_name
    with xls_path.open("wb") as f:
        attribute_xls.file.seek(0)
        shutil.copyfileobj(attribute_xls.file, f)
    shp_extract_dir = out_dir / "shp"
    shp_extract_dir.mkdir(exist_ok=True)
    if not zipfile.is_zipfile(str(shpzip_path)):
        return {"error": "not_a_zip_file", "filename": shpzip_name, "size": os.path.getsize(shpzip_path)}
    try:
        with zipfile.ZipFile(str(shpzip_path), 'r') as zf:
            for info in zf.infolist():
                name = info.filename
                fixed = name
                if not (info.flag_bits & 0x800):
                    for enc in ("utf-8", "gbk", "cp936"):
                        try:
                            fixed = name.encode("cp437").decode(enc)
                            break
                        except Exception:
                            pass
                target_path = shp_extract_dir / fixed
                if info.is_dir() or name.endswith("/"):
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, target_path.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile:
        return {"error": "bad_zip_file", "filename": shpzip_name, "size": os.path.getsize(shpzip_path)}
    shp_candidates = list(shp_extract_dir.rglob("*.shp"))
    if not shp_candidates:
        return {"error": "no_shp_found_in_zip"}
    shp_path = shp_candidates[0]
    algo = importlib.import_module("submod.坡面物源算法.K因子")
    clipped_path = out_dir / "clipped.tif"
    attribute_tif_path = out_dir / "clipped_with_attributes.tif"
    k_tif_path = out_dir / "k因子.tif"
    # 处理raster_file：支持ZIP（如HWSD：hwsd.bil/.hdr/.prj等）
    raster_data_path = raster_path
    try:
        if zipfile.is_zipfile(str(raster_path)):
            raster_extract_dir = out_dir / "raster"
            raster_extract_dir.mkdir(exist_ok=True)
            try:
                with zipfile.ZipFile(str(raster_path), 'r') as zf:
                    for info in zf.infolist():
                        name = info.filename
                        fixed = name
                        if not (info.flag_bits & 0x800):
                            for enc in ("utf-8", "gbk", "cp936"):
                                try:
                                    fixed = name.encode("cp437").decode(enc)
                                    break
                                except Exception:
                                    pass
                        target_path = raster_extract_dir / fixed
                        if info.is_dir() or name.endswith("/"):
                            target_path.mkdir(parents=True, exist_ok=True)
                        else:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(info) as src, target_path.open("wb") as dst:
                                shutil.copyfileobj(src, dst)
            except zipfile.BadZipFile:
                return {"error": "bad_zip_file", "filename": raster_name, "size": os.path.getsize(raster_path)}
            # 优先选择 .bil，其次 .tif
            bil_candidates = list(raster_extract_dir.rglob("*.bil"))
            tif_candidates = list(raster_extract_dir.rglob("*.tif"))
            if bil_candidates:
                raster_data_path = bil_candidates[0]
            elif tif_candidates:
                raster_data_path = tif_candidates[0]
            else:
                return {"error": "no_raster_found_in_zip"}
    except Exception:
        pass

    clipped_raster = algo.clip_raster_with_shapefile(str(raster_data_path), str(shp_path), str(clipped_path))
    attribute_tif, attribute_csv = algo.create_raster_attribute_table(str(clipped_raster), str(xls_path), str(attribute_tif_path))
    k_tif, k_csv = algo.calculate_k_for_raster(str(attribute_tif), str(attribute_csv), str(k_tif_path))
    import rasterio as rio
    with rio.open(k_tif) as src:
        data = src.read(1).astype(np.float32)
        nodata = src.nodata
        if nodata is not None:
            data[data == nodata] = np.nan
        data[data == -9999] = np.nan
        k_stats = {
            "min": float(np.nanmin(data)) if np.isfinite(np.nanmin(data)) else None,
            "max": float(np.nanmax(data)) if np.isfinite(np.nanmax(data)) else None,
            "mean": float(np.nanmean(data)) if np.isfinite(np.nanmean(data)) else None
        }
    base = str(request.base_url).rstrip("/")
    def url(name): return f"{base}/files/{uid}_k_factor/{name}"
    return {
        "id": uid,
        "raster_url": url(raster_name),
        "shp_zip_url": url(shpzip_name),
        "attribute_xls_url": url(xls_name),
        "clipped_tif_url": url(Path(clipped_path).name),
        "attribute_tif_url": url(Path(attribute_tif).name),
        "attribute_csv_url": url(Path(attribute_csv).name),
        "k_tif_url": url(Path(k_tif).name),
        "k_values_csv_url": url(Path(k_csv).name),
        "k_stats": k_stats
    }

@router.post("/ls-factor")
async def ls_factor(dem_file: UploadFile = File(...), target_resolution: float = Form(None), resample_method: str = Form("average"), chunk_size: int = Form(500), request: Request = None):
    uid = uuid.uuid4().hex
    out_dir = outputs_dir / f"{uid}_ls_factor"
    out_dir.mkdir(exist_ok=True)
    dem_name = f"{uid}_{Path(dem_file.filename).name}"
    dem_path = out_dir / dem_name
    with dem_path.open("wb") as f:
        dem_file.file.seek(0)
        shutil.copyfileobj(dem_file.file, f)
    dem_data_path = dem_path
    try:
        if zipfile.is_zipfile(str(dem_path)):
            dem_extract_dir = out_dir / "dem"
            dem_extract_dir.mkdir(exist_ok=True)
            try:
                with zipfile.ZipFile(str(dem_path), 'r') as zf:
                    for info in zf.infolist():
                        name = info.filename
                        fixed = name
                        if not (info.flag_bits & 0x800):
                            for enc in ("utf-8", "gbk", "cp936"):
                                try:
                                    fixed = name.encode("cp437").decode(enc)
                                    break
                                except Exception:
                                    pass
                        target_path = dem_extract_dir / fixed
                        if info.is_dir() or name.endswith("/"):
                            target_path.mkdir(parents=True, exist_ok=True)
                        else:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(info) as src, target_path.open("wb") as dst:
                                shutil.copyfileobj(src, dst)
            except zipfile.BadZipFile:
                return {"error": "bad_zip_file", "filename": dem_name, "size": os.path.getsize(dem_path)}
            tif_candidates = list(dem_extract_dir.rglob("*.tif")) + list(dem_extract_dir.rglob("*.tiff"))
            if tif_candidates:
                dem_data_path = tif_candidates[0]
            else:
                return {"error": "no_tif_found_in_zip"}
    except Exception:
        pass
    algo = importlib.import_module("submod.坡面物源算法.LS因子")
    ls_tif_path = out_dir / "LS因子.tif"
    import rasterio as rio
    try:
        # with rio.open(str(dem_data_path)) as src:
        #     transform = src.transform
        #     cell_size = abs(transform.a)
        cell_size = 0.1
    except Exception:
        cell_size = 0.1
    result_file = algo.calculate_ls_factor(str(dem_data_path), str(ls_tif_path), cell_size=cell_size, chunk_size=int(chunk_size) if chunk_size else 500, target_resolution=target_resolution, resample_method=resample_method or "average")
    log_path = Path(str(ls_tif_path).replace(".tif", "_log.txt"))
    ls_stats = None
    if result_file and Path(result_file).exists():
        with rio.open(str(ls_tif_path)) as src:
            data = src.read(1).astype(np.float32)
            nodata = src.nodata
            if nodata is not None:
                data[data == nodata] = np.nan
            data[data == -9999] = np.nan
            ls_stats = {
                "min": float(np.nanmin(data)) if np.isfinite(np.nanmin(data)) else None,
                "max": float(np.nanmax(data)) if np.isfinite(np.nanmax(data)) else None,
                "mean": float(np.nanmean(data)) if np.isfinite(np.nanmean(data)) else None
            }
    base = str(request.base_url).rstrip("/")
    def url(name): return f"{base}/files/{uid}_ls_factor/{name}"
    return {
        "id": uid,
        "dem_url": url(dem_name),
        "ls_tif_url": url(Path(ls_tif_path).name),
        "log_url": url(Path(log_path).name),
        "ls_stats": ls_stats
    }

@router.post("/p-factor/prepare")
async def p_factor_prepare(category_tif: UploadFile = File(...), request: Request = None):
    uid = uuid.uuid4().hex
    out_dir = outputs_dir / f"{uid}_p_factor"
    out_dir.mkdir(exist_ok=True)
    cat_name = f"{uid}_{Path(category_tif.filename).name}"
    cat_path = out_dir / cat_name
    with cat_path.open("wb") as f:
        category_tif.file.seek(0)
        shutil.copyfileobj(category_tif.file, f)
    tif_path = None
    if zipfile.is_zipfile(str(cat_path)):
        extract_dir = out_dir / "cat"
        extract_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(str(cat_path), 'r') as zf:
                for info in zf.infolist():
                    name = info.filename
                    fixed = name
                    if not (info.flag_bits & 0x800):
                        for enc in ("utf-8", "gbk", "cp936"):
                            try:
                                fixed = name.encode("cp437").decode(enc)
                                break
                            except Exception:
                                pass
                    target_path = extract_dir / fixed
                    if info.is_dir() or name.endswith("/"):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, target_path.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
        except zipfile.BadZipFile:
            return {"error": "bad_zip_file", "filename": cat_name, "size": os.path.getsize(cat_path)}
        candidates = list(extract_dir.rglob("*.tif")) + list(extract_dir.rglob("*.tiff"))
        if candidates:
            tif_path = candidates[0]
        else:
            return {"error": "no_tif_found_in_zip"}
    else:
        tif_path = cat_path
    algo = importlib.import_module("submod.坡面物源算法.P因子")
    values = algo.prepare_p_values(str(tif_path))
    base = str(request.base_url).rstrip("/")
    def url(name): return f"{base}/files/{uid}_p_factor/{name}"
    return {
        "id": uid,
        "category_tif_url": url(cat_name),
        "values": [int(v) for v in values if int(v) != 255]
    }

@router.post("/p-factor/apply")
async def p_factor_apply(category_tif: UploadFile = File(...), value_p_mapping: str = Form(...), request: Request = None):
    uid = uuid.uuid4().hex
    out_dir = outputs_dir / f"{uid}_p_factor"
    out_dir.mkdir(exist_ok=True)
    cat_name = f"{uid}_{Path(category_tif.filename).name}"
    cat_path = out_dir / cat_name
    with cat_path.open("wb") as f:
        category_tif.file.seek(0)
        shutil.copyfileobj(category_tif.file, f)
    try:
        mapping = json.loads(value_p_mapping)
    except Exception:
        return {"error": "invalid_mapping_json"}
    tif_path = None
    if zipfile.is_zipfile(str(cat_path)):
        extract_dir = out_dir / "cat"
        extract_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(str(cat_path), 'r') as zf:
                for info in zf.infolist():
                    name = info.filename
                    fixed = name
                    if not (info.flag_bits & 0x800):
                        for enc in ("utf-8", "gbk", "cp936"):
                            try:
                                fixed = name.encode("cp437").decode(enc)
                                break
                            except Exception:
                                pass
                    target_path = extract_dir / fixed
                    if info.is_dir() or name.endswith("/"):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, target_path.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
        except zipfile.BadZipFile:
            return {"error": "bad_zip_file", "filename": cat_name, "size": os.path.getsize(cat_path)}
        candidates = list(extract_dir.rglob("*.tif")) + list(extract_dir.rglob("*.tiff"))
        if candidates:
            tif_path = candidates[0]
        else:
            return {"error": "no_tif_found_in_zip"}
    else:
        tif_path = cat_path
    algo = importlib.import_module("submod.坡面物源算法.P因子")
    output_tif = out_dir / "P因子.tif"
    result = algo.apply_p_mapping(str(tif_path), str(output_tif), mapping)
    attr_path = Path(result.get("attribute_table"))
    attr_zip = out_dir / "attributes.zip"
    if attr_path.exists():
        stem = attr_path.with_suffix("").name
        folder = attr_path.parent
        with zipfile.ZipFile(str(attr_zip), "w", zipfile.ZIP_DEFLATED) as zf:
            for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                fpath = folder / f"{stem}{ext}"
                if fpath.exists():
                    zf.write(str(fpath), arcname=f"{stem}{ext}")
    base = str(request.base_url).rstrip("/")
    def url(name): return f"{base}/files/{uid}_p_factor/{name}"
    return {
        "id": uid,
        "category_tif_url": url(cat_name),
        "p_tif_url": url(Path(output_tif).name),
        "attributes_zip_url": url(Path(attr_zip).name),
        "mapping_used": result.get("mapping_used")
    }

@router.post("/r-factor")
async def r_factor(years_zip: List[UploadFile] = File(...), shp_zip: UploadFile = File(...), scale_factor: float = Form(0.1), request: Request = None):
    uid = uuid.uuid4().hex
    out_dir = outputs_dir / f"{uid}_r_factor"
    out_dir.mkdir(exist_ok=True)
    def save_upload(up: UploadFile, name_suffix: str):
        fname = f"{uid}_{Path(up.filename).name}"
        fpath = out_dir / fname
        with fpath.open("wb") as f:
            up.file.seek(0)
            shutil.copyfileobj(up.file, f)
        return fname, fpath
    year_zip_infos = []
    for i, up in enumerate(years_zip):
        name, path = save_upload(up, f"y{i+1}")
        year_zip_infos.append((name, path))
    shp_name, shp_zip_path = save_upload(shp_zip, "shp")
    def extract_zip(zpath: Path, target_dir: Path):
        target_dir.mkdir(exist_ok=True)
        if not zipfile.is_zipfile(str(zpath)):
            return {"error": "not_a_zip_file", "filename": zpath.name, "size": os.path.getsize(zpath)}, None
        try:
            with zipfile.ZipFile(str(zpath), 'r') as zf:
                for info in zf.infolist():
                    name = info.filename
                    fixed = name
                    if not (info.flag_bits & 0x800):
                        for enc in ("utf-8", "gbk", "cp936"):
                            try:
                                fixed = name.encode("cp437").decode(enc)
                                break
                            except Exception:
                                pass
                    target_path = target_dir / fixed
                    if info.is_dir() or name.endswith("/"):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, target_path.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
        except zipfile.BadZipFile:
            return {"error": "bad_zip_file", "filename": zpath.name, "size": os.path.getsize(zpath)}, None
        return None, target_dir
    year_dirs = []
    for idx, (name, path) in enumerate(year_zip_infos, start=1):
        err, ydir = extract_zip(path, out_dir / f"year{idx}")
        if err:
            return err
        year_dirs.append((name, ydir))
    err3, shp_dir = extract_zip(shp_zip_path, out_dir / "shp")
    if err3:
        return err3
    for _, ydir in year_dirs:
        tifs = list(ydir.rglob("*.tif")) + list(ydir.rglob("*.tiff"))
        if len(tifs) < 12:
            return {"error": "insufficient_monthly_tifs", "year_dir": str(ydir), "count": len(tifs)}
    shp_candidates = list(shp_dir.rglob("*.shp"))
    if not shp_candidates:
        return {"error": "no_shp_found_in_zip"}
    shp_path = shp_candidates[0]
    algo = importlib.import_module("submod.坡面物源算法.R因子")
    R_tif_path = out_dir / "R因子.tif"
    folder_paths = [str(ydir) for _, ydir in year_dirs]
    algo.calculate_rainfall_erosion_factor(folder_paths, str(shp_path), str(R_tif_path), scale_factor=scale_factor)
    import rasterio as rio
    R_stats = None
    if R_tif_path.exists():
        with rio.open(str(R_tif_path)) as src:
            data = src.read(1).astype(np.float32)
            nodata = src.nodata
            if nodata is not None:
                data[data == nodata] = np.nan
            R_stats = {
                "min": float(np.nanmin(data)) if np.isfinite(np.nanmin(data)) else None,
                "max": float(np.nanmax(data)) if np.isfinite(np.nanmax(data)) else None,
                "mean": float(np.nanmean(data)) if np.isfinite(np.nanmean(data)) else None
            }
    base = str(request.base_url).rstrip("/")
    def url(name): return f"{base}/files/{uid}_r_factor/{name}"
    return {
        "id": uid,
        "years_zip_url": [url(name) for name, _ in year_zip_infos],
        "shp_zip_url": url(shp_name),
        "r_tif_url": url(Path(R_tif_path).name),
        "r_stats": R_stats
    }
