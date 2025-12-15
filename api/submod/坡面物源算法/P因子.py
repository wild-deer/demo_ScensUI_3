from osgeo import gdal, ogr
import numpy as np
import os
import tempfile

def add_field_and_remap(input_tif, output_tif):
    """
    为TIF文件添加字段P，并在终端交互式输入P值
    
    参数:
    input_tif -- 输入TIF文件路径
    output_tif -- 输出TIF文件路径
    """
    # 打开原始栅格文件
    src_ds = gdal.Open(input_tif)
    if src_ds is None:
        raise Exception(f"无法打开输入文件: {input_tif}")

    # 获取栅格属性和数据
    band = src_ds.GetRasterBand(1)
    raster_data = band.ReadAsArray()
    nodata = band.GetNoDataValue()

    # 获取所有唯一值
    unique_values = np.unique(raster_data)
    unique_values = unique_values[~np.isnan(unique_values)]  # 移除NaN值
    
    # 打印唯一值列表
    print("发现以下唯一值:")
    for i, value in enumerate(sorted(unique_values)):
        # 标记NODATA值(255)
        if int(value) == 255:
            print(f"{i+1}. Value = {int(value)} (NODATA值，跳过)")
        else:
            print(f"{i+1}. Value = {int(value)}")
    
    # 创建映射字典
    value_p_mapping = {}
    
    # 交互式输入P值
    print("\n请为每个Value输入对应的P值（跳过NODATA值255）:")
    for value in sorted(unique_values):
        int_value = int(value)
        
        # 跳过NODATA值255
        if int_value == 255:
            print(f"跳过Value=255 (NODATA值)")
            continue
            
        while True:
            try:
                p_value = input(f"请输入Value={int_value}对应的P值: ")
                # 允许输入小数
                if '.' in p_value:
                    p_value = float(p_value)
                else:
                    p_value = int(p_value)
                value_p_mapping[int_value] = p_value
                break
            except ValueError:
                print("输入无效，请输入数字值")
    
    # 创建新的栅格文件
    driver = gdal.GetDriverByName('GTiff')
    dst_ds = driver.Create(
        output_tif,
        src_ds.RasterXSize,
        src_ds.RasterYSize,
        1,  # 波段数量
        gdal.GDT_Float32 if any(isinstance(v, float) for v in value_p_mapping.values()) else gdal.GDT_Int32
    )
    dst_ds.SetProjection(src_ds.GetProjection())
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())
    dst_band = dst_ds.GetRasterBand(1)

    # 创建像素值映射
    remapped_data = np.zeros_like(raster_data, dtype=np.float32)
    for value in unique_values:
        int_value = int(value)
        mask = raster_data == value
        
        # 跳过NODATA值255
        if int_value == 255:
            # 保留原始值255
            remapped_data[mask] = value
        else:
            remapped_data[mask] = value_p_mapping.get(int_value, nodata)

    # 写入新数据
    dst_band.WriteArray(remapped_data)
    if nodata is not None:
        dst_band.SetNoDataValue(float(nodata))
    dst_band.FlushCache()

    # 创建属性表（使用临时Shapefile）
    temp_dir = tempfile.mkdtemp()
    temp_shp = os.path.join(temp_dir, "attributes.shp")
    
    # 创建属性表Shapefile
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.CreateDataSource(temp_shp)
    layer = ds.CreateLayer("attributes", geom_type=ogr.wkbNone)
    
    # 添加字段
    field_value = ogr.FieldDefn("Value", ogr.OFTInteger)
    layer.CreateField(field_value)
    
    field_p = ogr.FieldDefn("P", ogr.OFTReal)
    layer.CreateField(field_p)
    
    # 添加记录
    for value in sorted(unique_values):
        int_value = int(value)
        
        # 跳过NODATA值255
        if int_value == 255:
            continue
            
        p_value = value_p_mapping.get(int_value, -9999)
        
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
    for value, p in value_p_mapping.items():
        print(f"Value {value} -> P {p}")

    # 清理资源
    src_ds = None
    dst_ds = None

# 在代码中直接指定文件路径
if __name__ == "__main__":
    # 在这里直接设置输入和输出文件路径
    input_file = r"F:\名人堂\许英杰项目\泥石流物源体积计算\坡面物源侵蚀\代码\土地利用因子P\c2020_Clip1.tif"
    output_file = r"F:\名人堂\许英杰项目\泥石流物源体积计算\坡面物源侵蚀\代码\土地利用因子P\P因子.tif"
    
    # 检查文件路径是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在 - {input_file}")
        exit(1)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    add_field_and_remap(input_file, output_file)