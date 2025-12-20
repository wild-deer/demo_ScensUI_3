

# API 接口文档

## 服务信息
- 基础地址：`http://<host>:25376/`
- 静态文件：`GET /files/*`，所有输出文件均可通过返回的 URL 直接访问
- 所有上传均使用 `multipart/form-data`

## 崩滑物源 SLBL
- 接口：`POST /process-slbl`
- 入参
  - `file`：`UploadFile`，输入 DEM `tif`
  - `max_iter`：`Form[int]`，最大迭代次数
- 返回
  - `id`：唯一标识
  - `volume_diff_m3`：体积差（单位：立方米）
  - `calculated_tif_url`：计算后的 SLBL `tif` 链接
  - `reprojected_tif_url`：重投影结果 `tif` 链接
  - `input_tif_url`：原始上传 `tif` 链接

## 坡面物源 C 因子
- 接口：`POST /c-factor`
- 入参
  - `ndvi_file`：`UploadFile`，NDVI `tif`
  - `shp_zip`：`UploadFile`，裁剪范围 Zip（含 `*.shp/.dbf/.shx/.prj`）
- 返回
  - `id`
  - `ndvi_tif_url`
  - `shp_zip_url`
  - `clipped_ndvi_tif_url`：`裁剪后ndvi.tif`
  - `f_tif_url`：`植被覆盖度f.tif`
  - `c_tif_url`：`C因子.tif`
  - `report_url`：`statistics_report.txt`
  - `visualization_url`：`vegetation_analysis_results.png`
  - `c_stats`：`{ min, max, mean }`
  - `f_stats`：`{ min, max, mean }`

## 坡面物源 K 因子
- 接口：`POST /k-factor`
- 入参
  - `raster_file`：`UploadFile`，HWSD 等栅格或 Zip（Zip 自动解压并优先选 `*.bil`，其次 `*.tif`）
  - `shp_zip`：`UploadFile`，裁剪范围 Zip
  - `attribute_xls`：`UploadFile`，属性表 Excel（`xls/xlsx`）
- 返回
  - `id`
  - `raster_url`
  - `shp_zip_url`
  - `attribute_xls_url`
  - `clipped_tif_url`：`clipped.tif`
  - `attribute_tif_url`：`clipped_with_attributes.tif`
  - `attribute_csv_url`：`*_attributes.csv`
  - `k_tif_url`：`k因子.tif`
  - `k_values_csv_url`：K 值统计表
  - `k_stats`：`{ min, max, mean }`

## 坡面物源 LS 因子
- 接口：`POST /ls-factor`
- 入参
  - `dem_file`：`UploadFile`，DEM `tif` 或 Zip（Zip 自动解压选 `*.tif`）
  - `target_resolution`：`Form[float]`，可选，重采样分辨率（米）
  - `resample_method`：`Form[str]`，可选，`average/bilinear/cubic`，默认 `average`
  - `chunk_size`：`Form[int]`，可选，默认 `500`
- 返回
  - `id`
  - `dem_url`
  - `ls_tif_url`：`LS因子.tif`
  - `log_url`：`LS因子_log.txt`
  - `ls_stats`：`{ min, max, mean }`

## 坡面物源 P 因子（准备）
- 接口：`POST /p-factor/prepare`
- 入参
  - `category_tif`：`UploadFile`，分类栅格 Zip（自动解压定位 `*.tif`）
- 返回
  - `id`
  - `category_tif_url`：上传 Zip 链接
  - `values`：可填写 P 值的分类列表（自动跳过 `255`）

## 坡面物源 P 因子（应用）
- 接口：`POST /p-factor/apply`
- 入参
  - `category_tif`：`UploadFile`，分类栅格 Zip（自动解压定位 `*.tif`）
  - `value_p_mapping`：`Form[str]`，JSON 字符串，如 `{"1":0.5,"2":1}`
- 返回
  - `id`
  - `category_tif_url`：上传 Zip 链接
  - `p_tif_url`：输出 `P因子.tif`
  - `attributes_zip_url`：属性表打包 Zip（含 `attributes.shp/.dbf/.shx/.prj/.cpg` 存在则打包）
  - `mapping_used`：最终使用的映射（已标准化）

## 坡面物源 R 因子
- 接口：`POST /r-factor`
- 入参
  - `years_zip`：`List[UploadFile]`，多个年份的降雨量 Zip（每个年份需含 12 个 `*.tif/*.tiff` 月文件，任意层级）
  - `shp_zip`：`UploadFile`，裁剪范围 Zip
  - `scale_factor`：`Form[float]`，默认 `0.1`（如原始数据被放大 10 倍）
- 返回
  - `id`
  - `years_zip_url`：列表，上传年份 Zip 的链接
  - `shp_zip_url`
  - `r_tif_url`：`R因子.tif`
  - `r_stats`：`{ min, max, mean }`
