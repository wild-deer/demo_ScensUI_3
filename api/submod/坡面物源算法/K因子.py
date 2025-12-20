import rasterio
from rasterio.mask import mask
from rasterio.plot import show
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from osgeo import gdal, osr
import math

def clip_raster_with_shapefile(raster_path, shapefile_path, output_path):
    """
    使用shp文件裁剪栅格数据
    """
    # 1. 打开栅格文件
    with rasterio.open(raster_path) as src:
        # 获取原始NODATA值
        src_nodata = src.nodata
        
        # 获取数据类型
        dtype = src.dtypes[0]
        
        # 根据数据类型选择合适的NODATA值
        if src_nodata is None:
            if dtype == 'uint8':
                src_nodata = 255
            elif dtype == 'uint16':
                src_nodata = 65535
            elif dtype == 'int16':
                src_nodata = -32768
            elif dtype == 'float32':
                src_nodata = -9999.0
            else:
                src_nodata = -9999
        
        # 2. 读取shp文件
        gdf = gpd.read_file(shapefile_path)
        
        # 3. 确保shp文件与栅格使用相同的坐标系
        if gdf.crs != src.crs:
            gdf = gdf.to_crs(src.crs)
        
        # 4. 获取shp文件的几何对象
        geometries = gdf.geometry.values
        
        # 5. 使用shp文件裁剪栅格
        out_image, out_transform = mask(
            src, 
            geometries,
            crop=True,
            all_touched=True,
            nodata=src_nodata
        )
        
        # 6. 更新元数据
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "crs": src.crs,
            "nodata": src_nodata
        })
        
        # 7. 保存裁剪后的栅格
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)
    
    return output_path

def create_raster_attribute_table(raster_path, attribute_xls_path, output_path):
    """
    为栅格文件创建属性表，添加四个浮点型字段：SAND, SILT, CLAY, C
    """
    # 读取土壤属性XLS文件
    if not os.path.exists(attribute_xls_path):
        print(f"警告: 找不到土壤属性文件 {attribute_xls_path}")
        attribute_df = pd.DataFrame(columns=['MU_GLOBAL', 'T_SAND', 'T_SILT', 'T_CLAY', 'T_OC'])
    else:
        attribute_df = pd.read_excel(attribute_xls_path)
        print(f"成功读取土壤属性文件，共 {len(attribute_df)} 条记录")
    
    # 打开输入栅格
    src_ds = gdal.Open(raster_path, gdal.GA_ReadOnly)
    band = src_ds.GetRasterBand(1)
    data = band.ReadAsArray()
    
    # 获取唯一值
    unique_values = np.unique(data)
    print(f"栅格中有 {len(unique_values)} 个唯一值")
    
    # 创建属性表DataFrame
    rat_df = pd.DataFrame(columns=['Value', 'Count', 'SAND', 'SILT', 'CLAY', 'C'])
    
    # 计算每个值的像素数量并添加属性
    row_index = 0
    for value in unique_values:
        if value == band.GetNoDataValue():
            continue
            
        # 计算该值的像素数量
        mask = (data == value)
        count = np.count_nonzero(mask)
        
        # 初始化属性值
        sand = -9999
        silt = -9999
        clay = -9999
        c = -9999
        
        if not attribute_df.empty:
            matches = attribute_df[attribute_df['MU_GLOBAL'] == value]
            
            if not matches.empty:
                match = matches.iloc[0]
                
                if 'T_SAND' in match:
                    sand = match['T_SAND']
                if 'T_SILT' in match:
                    silt = match['T_SILT']
                if 'T_CLAY' in match:
                    clay = match['T_CLAY']
                if 'T_OC' in match:
                    c = match['T_OC']
                
                print(f"为值 {value} 找到属性: SAND={sand}, SILT={silt}, CLAY={clay}, C={c}")
        
        # 添加到DataFrame
        rat_df.loc[row_index] = [value, count, sand, silt, clay, c]
        row_index += 1
    
    # 保存属性表为CSV文件
    csv_path = output_path.replace('.tif', '_attributes.csv')
    rat_df.to_csv(csv_path, index=False)
    print(f"属性表已保存为CSV文件: {csv_path}")
    
    # 创建新的栅格文件
    driver = gdal.GetDriverByName('GTiff')
    dst_ds = driver.CreateCopy(output_path, src_ds)
    dst_band = dst_ds.GetRasterBand(1)
    
    # 创建栅格属性表
    rat = gdal.RasterAttributeTable()
    
    # 添加字段
    rat.CreateColumn('Value', gdal.GFT_Integer, gdal.GFU_Generic)
    rat.CreateColumn('Count', gdal.GFT_Integer, gdal.GFU_PixelCount)
    rat.CreateColumn('SAND', gdal.GFT_Real, gdal.GFU_Generic)
    rat.CreateColumn('SILT', gdal.GFT_Real, gdal.GFU_Generic)
    rat.CreateColumn('CLAY', gdal.GFT_Real, gdal.GFU_Generic)
    rat.CreateColumn('C', gdal.GFT_Real, gdal.GFU_Generic)
    
    # 填充属性表
    for index, row in rat_df.iterrows():
        rat.SetValueAsInt(index, 0, int(row['Value']))
        rat.SetValueAsInt(index, 1, int(row['Count']))
        rat.SetValueAsDouble(index, 2, float(row['SAND']))
        rat.SetValueAsDouble(index, 3, float(row['SILT']))
        rat.SetValueAsDouble(index, 4, float(row['CLAY']))
        rat.SetValueAsDouble(index, 5, float(row['C']))
    
    rat.SetRowCount(len(rat_df))
    dst_band.SetDefaultRAT(rat)
    dst_ds.FlushCache()
    
    src_ds = None
    dst_ds = None
    
    print(f"属性表创建完成，共添加 {len(rat_df)} 行")
    return output_path, csv_path

def calculate_k_epic(sand, silt, clay, c):
    """
    计算K_EPIC值
    根据图片中的公式：K_EPIC = {0.2 + 0.3exp[-0.0256SAN(1-SIL/100)]} × (SIL/(CLA+SIL))^0.3 × 
    (1 - 0.25C/(C+exp(3.72-2.95C))) × (1 - 0.7(1-SAN)/((1-SAN)+exp(22.9(1-SAN)-5.51)))
    
    注意：SAND, SILT, CLAY, C需要先除以100转换为小数形式
    """
    # 处理缺失值
    if sand == -9999 or silt == -9999 or clay == -9999 or c == -9999:
        return np.nan
    
    try:
        # 将百分比转换为小数
        sand_decimal = sand / 100.0
        silt_decimal = silt / 100.0
        clay_decimal = clay / 100.0
        c_decimal = c / 100.0
        
        # 第一部分：0.2 + 0.3exp[-0.0256SAN(1-SIL/100)]
        # 注意：公式中SIL已经是百分比，需要除以100，但我们已经转换为小数
        part1 = 0.2 + 0.3 * math.exp(-0.0256 * sand * (1 - silt_decimal))
        
        # 第二部分：(SIL/(CLA+SIL))^0.3
        if clay + silt == 0:
            part2 = 0
        else:
            part2 = (silt / (clay + silt)) ** 0.3
        
        # 第三部分：1 - 0.25C/(C+exp(3.72-2.95C))
        denominator3 = c + math.exp(3.72 - 2.95 * c)
        if denominator3 == 0:
            part3 = 1
        else:
            part3 = 1 - (0.25 * c) / denominator3
        
        # 第四部分：1 - 0.7(1-SAN)/((1-SAN)+exp(22.9(1-SAN)-5.51))
        one_minus_sand = 1 - sand_decimal
        denominator4 = one_minus_sand + math.exp(22.9 * one_minus_sand - 5.51)
        if denominator4 == 0:
            part4 = 1
        else:
            part4 = 1 - (0.7 * one_minus_sand) / denominator4
        
        # 计算K_EPIC
        k_epic = part1 * part2 * part3 * part4
        return k_epic
    
    except (ValueError, ZeroDivisionError, OverflowError):
        return np.nan

def calculate_k(k_epic):
    """
    计算K值
    根据图片中的公式：K = (-0.01383 + 0.51575 × K_EPIC) × 0.1317
    """
    if np.isnan(k_epic):
        return np.nan
    
    try:
        k = (-0.01383 + 0.51575 * k_epic) * 0.1317
        return k
    except:
        return np.nan

def calculate_k_for_raster(input_tif_path, attribute_csv_path, output_tif_path):
    """
    为栅格文件计算K值
    """
    # 读取属性表CSV文件
    if not os.path.exists(attribute_csv_path):
        raise FileNotFoundError(f"找不到属性表文件: {attribute_csv_path}")
    
    attribute_df = pd.read_csv(attribute_csv_path)
    print(f"成功读取属性表，共 {len(attribute_df)} 行")
    
    # 创建值到属性的映射字典
    value_to_attributes = {}
    for _, row in attribute_df.iterrows():
        value = row['Value']
        value_to_attributes[value] = {
            'SAND': row['SAND'],
            'SILT': row['SILT'], 
            'CLAY': row['CLAY'],
            'C': row['C']
        }
    
    # 读取输入栅格文件
    with rasterio.open(input_tif_path) as src:
        data = src.read(1)
        nodata = src.nodata
        
        profile = src.profile
        profile.update(dtype=rasterio.float32, count=1, nodata=-9999)
        
        k_array = np.full(data.shape, -9999, dtype=np.float32)
        
        unique_values = np.unique(data)
        print(f"处理 {len(unique_values)} 个唯一值")
        
        k_values = {}
        for value in unique_values:
            if value == nodata:
                continue
                
            if value in value_to_attributes:
                attrs = value_to_attributes[value]
                sand = attrs['SAND']
                silt = attrs['SILT']
                clay = attrs['CLAY']
                c = attrs['C']
                
                k_epic = calculate_k_epic(sand, silt, clay, c)
                k_val = calculate_k(k_epic)
                
                k_values[value] = k_val
                print(f"值 {value}: SAND={sand}, SILT={silt}, CLAY={clay}, C={c} -> K_EPIC={k_epic:.6f}, K={k_val:.6f}")
            else:
                k_values[value] = np.nan
        
        # 将K值映射到栅格数组
        for value, k_val in k_values.items():
            mask = (data == value)
            if not np.isnan(k_val):
                k_array[mask] = k_val
            else:
                k_array[mask] = -9999
        
        if nodata is not None:
            k_array[data == nodata] = -9999
        
        # 保存K值栅格
        with rasterio.open(output_tif_path, 'w', **profile) as dst:
            dst.write(k_array, 1)
        
        print(f"K值计算完成，结果已保存至: {output_tif_path}")
        
        # 创建K值属性表CSV
        k_csv_path = output_tif_path.replace('.tif', '_k_values.csv')
        k_df = pd.DataFrame({
            'Value': list(k_values.keys()),
            'K_EPIC': [calculate_k_epic(
                value_to_attributes[v]['SAND'] if v in value_to_attributes else -9999,
                value_to_attributes[v]['SILT'] if v in value_to_attributes else -9999,
                value_to_attributes[v]['CLAY'] if v in value_to_attributes else -9999,
                value_to_attributes[v]['C'] if v in value_to_attributes else -9999
            ) if v in value_to_attributes else np.nan for v in k_values.keys()],
            'K': list(k_values.values())
        })
        k_df.to_csv(k_csv_path, index=False)
        print(f"K值属性表已保存至: {k_csv_path}")
        
        return output_tif_path, k_csv_path

def visualize_results(original_raster, clipped_raster, k_raster, shapefile_path):
    """
    可视化原始栅格、裁剪后的栅格、K值栅格和shp文件
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
    
    # 绘制原始栅格
    with rasterio.open(original_raster) as src:
        show(src, ax=ax1, title='原始栅格数据', cmap='viridis')
        gdf = gpd.read_file(shapefile_path)
        if gdf.crs != src.crs:
            gdf = gdf.to_crs(src.crs)
        gdf.boundary.plot(ax=ax1, edgecolor='red', linewidth=2)
    
    # 绘制裁剪后的栅格
    with rasterio.open(clipped_raster) as src:
        show(src, ax=ax2, title='裁剪后的栅格数据', cmap='viridis')
        gdf.boundary.plot(ax=ax2, edgecolor='red', linewidth=2)
    
    # 绘制K值栅格
    with rasterio.open(k_raster) as src:
        show(src, ax=ax3, title='土壤可蚀性因子K', cmap='viridis')
        gdf.boundary.plot(ax=ax3, edgecolor='red', linewidth=2)
    
    plt.tight_layout()
    plt.savefig('raster_comparison.png', dpi=300)
    plt.show()

def main():
    # 设置文件路径
    raster_path = "./input/坡面物源算法/K因子/hwsd.bil"
    shapefile_path = "./input/坡面物源算法/K因子/边界轮廓/边界轮廓.shp"
    attribute_xls_path = "./input/坡面物源算法/K因子/HWSD_DATA.xls"
    clipped_path = 'clipped_HWSD.tif'
    attribute_tif_path = 'clipped_HWSD_with_attributes.tif'
    k_tif_path = 'k因子.tif'
    
    # 检查文件是否存在
    if not os.path.exists(raster_path):
        print(f"错误: 找不到栅格文件 {raster_path}")
        return
    
    if not os.path.exists(shapefile_path):
        print(f"错误: 找不到shp文件 {shapefile_path}")
        return
    
    # 执行裁剪
    print("开始裁剪栅格数据...")
    clipped_raster = clip_raster_with_shapefile(raster_path, shapefile_path, clipped_path)
    print(f"裁剪完成! 结果已保存至: {clipped_raster}")
    
    # 创建栅格属性表
    print("创建栅格属性表...")
    attribute_csv_path = clipped_path.replace('.tif', '_attributes.csv')
    attribute_tif, attribute_csv = create_raster_attribute_table(clipped_path, attribute_xls_path, attribute_tif_path)
    print(f"属性表创建完成! 结果已保存至: {attribute_tif}")
    
    # 计算K值
    print("计算土壤可蚀性因子K...")
    k_tif, k_csv = calculate_k_for_raster(attribute_tif, attribute_csv, k_tif_path)
    print(f"K值计算完成! 结果已保存至: {k_tif}")


if __name__ == "__main__":
    main()