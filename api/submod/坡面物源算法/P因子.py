from osgeo import gdal, ogr
import numpy as np
import os
import tempfile

def prepare_p_values(input_tif):
    """
    上半部分：提取需要填写 P 值的像元分类值列表（跳过 NODATA=255）
    
    参数:
    input_tif -- 输入 TIF 文件路径
    
    返回:
    List[int] -- 前端页面需要填写的 Value 列表
    """
    # 打开栅格并读取第一波段数据
    src_ds = gdal.Open(input_tif)
    if src_ds is None:
        raise Exception(f"无法打开输入文件: {input_tif}")
    band = src_ds.GetRasterBand(1)
    raster_data = band.ReadAsArray()
    # 计算唯一值并移除 NaN
    unique_values = np.unique(raster_data)
    unique_values = unique_values[~np.isnan(unique_values)]
    # 控制台打印用于调试与日志
    print("发现以下唯一值:")
    for i, value in enumerate(sorted(unique_values)):
        if int(value) == 255:
            print(f"{i+1}. Value = {int(value)} (NODATA值，跳过)")
        else:
            print(f"{i+1}. Value = {int(value)}")
    # 跳过 NODATA=255，生成可填写的值列表
    values_for_mapping = [int(v) for v in sorted(unique_values) if int(v) != 255]
    # 释放 GDAL 资源
    src_ds = None
    return values_for_mapping

def apply_p_mapping(input_tif, output_tif, value_p_mapping):
    """
    下半部分：根据页面提交的 Value→P 映射生成输出栅格与属性表
    
    参数:
    input_tif -- 输入 TIF 文件路径
    output_tif -- 输出 TIF 文件路径
    value_p_mapping -- 字典映射 {Value: P}，支持字符串或数字
    
    返回:
    dict -- 包含输出栅格路径、属性表路径与最终使用的映射
    """
    # 读取输入栅格与基本信息
    src_ds = gdal.Open(input_tif)
    if src_ds is None:
        raise Exception(f"无法打开输入文件: {input_tif}")
    band = src_ds.GetRasterBand(1)
    raster_data = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    unique_values = np.unique(raster_data)
    unique_values = unique_values[~np.isnan(unique_values)]
    # 规范化映射：键转 int，值支持字符串数字，最终为 float 或 int
    normalized_mapping = {}
    for k, v in value_p_mapping.items():
        ik = int(k)
        if isinstance(v, str):
            try:
                v = float(v) if "." in v else int(v)
            except ValueError:
                raise Exception(f"映射中存在无效P值: {k} -> {v}")
        normalized_mapping[ik] = float(v) if isinstance(v, float) else int(v)
    # 创建输出栅格，依据映射是否含有浮点决定数据类型
    driver = gdal.GetDriverByName('GTiff')
    dst_ds = driver.Create(
        output_tif,
        src_ds.RasterXSize,
        src_ds.RasterYSize,
        1,
        gdal.GDT_Float32 if any(isinstance(v, float) for v in normalized_mapping.values()) else gdal.GDT_Int32
    )
    dst_ds.SetProjection(src_ds.GetProjection())
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())
    dst_band = dst_ds.GetRasterBand(1)
    # 逐值重映射：255 保留原值；未提供的值写为 nodata
    remapped_data = np.zeros_like(raster_data, dtype=np.float32)
    for value in unique_values:
        int_value = int(value)
        mask = raster_data == value
        if int_value == 255:
            remapped_data[mask] = value
        else:
            remapped_data[mask] = normalized_mapping.get(int_value, nodata)
    # 写出栅格数据与 NoData
    dst_band.WriteArray(remapped_data)
    if nodata is not None:
        dst_band.SetNoDataValue(float(nodata))
    dst_band.FlushCache()
    # 创建属性表（临时 Shapefile），用于记录 Value 与 P
    temp_dir = tempfile.mkdtemp()
    temp_shp = os.path.join(temp_dir, "attributes.shp")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.CreateDataSource(temp_shp)
    layer = ds.CreateLayer("attributes", geom_type=ogr.wkbNone)
    field_value = ogr.FieldDefn("Value", ogr.OFTInteger)
    layer.CreateField(field_value)
    field_p = ogr.FieldDefn("P", ogr.OFTReal)
    layer.CreateField(field_p)
    # 写入每个有效 Value 的记录
    for value in sorted(unique_values):
        int_value = int(value)
        if int_value == 255:
            continue
        p_value = normalized_mapping.get(int_value, -9999)
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("Value", int_value)
        feature.SetField("P", float(p_value))
        layer.CreateFeature(feature)
        feature = None
    ds = None
    print(f"\n属性表已保存为: {temp_shp}")
    print("处理完成！输出文件:")
    print(f"栅格数据: {output_tif}")
    print(f"属性表: {temp_shp}")
    print("使用的映射关系:")
    for value, p in normalized_mapping.items():
        print(f"Value {value} -> P {p}")
    # 释放资源并返回结果信息
    src_ds = None
    dst_ds = None
    return {"output_tif": output_tif, "attribute_table": temp_shp, "mapping_used": normalized_mapping}

if __name__ == "__main__":
    # 示例：接口第一步只执行上半部分，返回可填写的 Value 列表
    input_file = r"./input/坡面物源算法/P因子/c2020_Clip1.tif"
    output_file = r"./output/因子.tif"
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在 - {input_file}")
        exit(1)
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    values = prepare_p_values(input_file)
    print(f"可填写P值的Value列表: {values}")
    value_p_mapping = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14, "15": 15, "16": 16, "17": 17, "18": 18, "19": 19, "20": 20, "21": 21, "22": 22, }

    # 先运行获取p值，再运行下面的函数输入对应的p值
    # apply_p_mapping(input_tif, output_tif, value_p_mapping):