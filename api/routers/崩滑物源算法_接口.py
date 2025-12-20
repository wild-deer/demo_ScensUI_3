from fastapi import APIRouter, UploadFile, File, Form, Request
from pathlib import Path
import os
import sys
import uuid
import shutil
import importlib
import numpy as np
import rasterio

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)


base_dir = Path(root_dir)
outputs_dir = base_dir / "outputs"
outputs_dir.mkdir(exist_ok=True)

@router.post("/process-slbl")
async def process_slbl(file: UploadFile = File(...), max_iter: int = Form(...), request: Request = None):
    uid = uuid.uuid4().hex
    in_name = f"{uid}_{Path(file.filename).stem}.tif"
    in_path = outputs_dir / in_name
    with in_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    
    algo = importlib.import_module("submod.崩滑物源算法")
    calc_name = f"{uid}_calculated_slbl_with_correction.tif"
    calc_path = outputs_dir / calc_name
    algo.main1(str(in_path), max_iter=max_iter, output_slbl_path=str(calc_path))
    reproj_name = f"{uid}_ReprojectImage.tif"
    reproj_path = outputs_dir / reproj_name
    algo.inputfilePath = str(calc_path)
    algo.referencefilefilePath = str(in_path)
    algo.outputfilePath = str(reproj_path)
    algo.ReprojectImages()
    valid_mask, elevation_diff, output_data = algo.compute_volume_difference()
    with rasterio.open(str(reproj_path)) as src:
        transform = src.transform
        pixel_area = abs(transform.a * transform.e)
    total_volume_diff = float(np.nansum(elevation_diff[valid_mask] * pixel_area))
    base = str(request.base_url).rstrip("/")
    return {
        "id": uid,
        "volume_diff_m3": total_volume_diff,
        "calculated_tif_url": f"{base}/files/{calc_name}",
        "reprojected_tif_url": f"{base}/files/{reproj_name}",
        "input_tif_url": f"{base}/files/{in_name}"
    }

