import os
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from glob import glob
import warnings
warnings.filterwarnings('ignore')

def calculate_rainfall_erosion_factor(folder_paths, shp_path, output_path, scale_factor=0.1):
    """
    计算降雨侵蚀因子R
    
    参数:
    folder_paths: 包含多个年份文件夹的路径列表
    shp_path: 裁剪用的shp文件路径
    output_path: 输出R因子TIFF文件路径
    scale_factor: 数据缩放因子，默认为1.0（不缩放）。如果数据被放大了10倍，可设为0.1
    """
    
    # 1. 读取shp文件并准备几何对象
    print("读取shp文件...")
    gdf = gpd.read_file(shp_path)
    
    # 确保几何对象是有效的GeoJSON格式
    if not gdf.geometry.is_valid.all():
        print("修复无效几何对象...")
        gdf.geometry = gdf.geometry.buffer(0)  # 修复无效几何
    
    # 获取GeoJSON格式的几何对象
    geometries = gdf.geometry.values
    if len(geometries) == 0:
        print("错误：shp文件中没有有效的几何对象")
        return
    
    print(f"找到 {len(folder_paths)} 个年份文件夹")
    print(f"使用缩放因子: {scale_factor}")
    
    # 2. 初始化存储数组
    monthly_data = {}  # 存储每个月的所有年份数据
    annual_totals = []  # 存储每年的年降雨总量
    nodata_mask = None  # 存储NODATA掩码
    
    # 3. 遍历每个年份文件夹
    for folder_path in folder_paths:
        folder_name = os.path.basename(folder_path)
        tif_files = glob(os.path.join(folder_path, "*.tif"))
        tif_files.sort()  # 确保按月份顺序
        
        if len(tif_files) != 12:
            print(f"警告: {folder_name} 文件夹中不是12个文件，跳过")
            continue
            
        print(f"处理 {folder_name}...")
        
        year_monthly_data = []
        
        # 处理每个月的tif文件
        for i, tif_file in enumerate(tif_files):
            month = i + 1
            
            try:
                with rasterio.open(tif_file) as src:
                    # 获取原始NODATA值
                    src_nodata = src.nodata
                    if src_nodata is None:
                        src_nodata = -9999  # 默认值
                    
                    # 裁剪数据 - 使用正确的几何对象
                    out_image, out_transform = mask(src, geometries, crop=True, all_touched=True)
                    monthly_data_arr = out_image[0]  # 取第一个波段
                    
                    # 应用缩放因子
                    if scale_factor != 1.0:
                        monthly_data_arr = monthly_data_arr * scale_factor
                    
                    # 创建当前文件的NODATA掩码
                    current_nodata_mask = (monthly_data_arr == src_nodata)
                    
                    # 更新全局NODATA掩码
                    if nodata_mask is None:
                        nodata_mask = current_nodata_mask
                    else:
                        nodata_mask = np.logical_or(nodata_mask, current_nodata_mask)
                    
                    # 将NODATA区域设为NaN，避免影响计算
                    monthly_data_arr[current_nodata_mask] = np.nan
                    
                    # 存储到对应的月份
                    if month not in monthly_data:
                        monthly_data[month] = []
                    monthly_data[month].append(monthly_data_arr)
                    
                    year_monthly_data.append(monthly_data_arr)
                    
            except Exception as e:
                print(f"处理 {tif_file} 时出错: {e}")
                continue
        
        # 计算该年的年降雨总量
        if year_monthly_data:
            # 使用nanmean忽略NaN值
            year_total = np.nansum(year_monthly_data, axis=0)
            annual_totals.append(year_total)
    
    if not monthly_data:
        print("没有找到有效的数据")
        return
    
    # 4. 计算月平均降雨量Pi和多年平均年降雨量P
    print("计算统计量...")
    
    # 计算每个月的月平均降雨量Pi
    Pi_avg = {}
    for month in range(1, 13):
        if month in monthly_data:
            # 对同一月份的所有年份数据求平均，忽略NaN
            monthly_arrays = monthly_data[month]
            Pi_avg[month] = np.nanmean(monthly_arrays, axis=0)
    
    # 计算多年平均年降雨量P
    if annual_totals:
        P_avg = np.nanmean(annual_totals, axis=0)
    else:
        print("无法计算年降雨量")
        return
    
    # 5. 使用Wischmeier公式计算R因子
    print("计算R因子...")
    
    # 初始化R_total为NaN数组
    R_total = np.full_like(P_avg, np.nan, dtype=np.float32)
    
    for month in range(1, 13):
        if month in Pi_avg:
            Pi = Pi_avg[month]
            
            # 创建有效掩码：Pi和P都不为NaN且大于0
            valid_mask = (~np.isnan(Pi)) & (~np.isnan(P_avg)) & (Pi > 0) & (P_avg > 0)
            
            # 只在有效区域计算
            if np.any(valid_mask):
                Pi_valid = Pi[valid_mask]
                P_valid = P_avg[valid_mask]
                
                # Wischmeier公式: R = 1.735 × 10^(1.5 × log10(Pi²/P) - 0.08188)
                log_term = 1.5 * np.log10((Pi_valid**2) / P_valid) - 0.08188
                R_valid = 1.735 * (10 ** log_term)
                
                # 将计算结果放入R_total
                R_total[valid_mask] = np.where(
                    np.isnan(R_total[valid_mask]),  # 如果当前位置是NaN
                    0,  # 设为0（因为后面会累加）
                    R_total[valid_mask]  # 否则保持原值
                )
                R_total[valid_mask] += R_valid
    
    # 6. 处理NODATA区域
    # 将NODATA区域设为原始NODATA值
    R_total[nodata_mask] = src_nodata
    
    # 7. 保存结果
    print("保存结果...")
    
    # 获取参考的元数据（使用第一个有效的tif文件）
    ref_tif = None
    for folder_path in folder_paths:
        tif_files = glob(os.path.join(folder_path, "*.tif"))
        if tif_files:
            ref_tif = tif_files[0]
            break
    
    if ref_tif:
        with rasterio.open(ref_tif) as src_ref:
            # 获取裁剪后的变换矩阵（使用第一个月份的数据作为参考）
            first_month_data = monthly_data[1][0] if 1 in monthly_data else None
            
            if first_month_data is not None:
                # 创建输出文件
                profile = src_ref.profile
                profile.update({
                    'dtype': rasterio.float32,
                    'count': 1,
                    'compress': 'lzw',
                    'nodata': src_nodata  # 设置NODATA值
                })
                
                # 更新变换矩阵为裁剪后的变换矩阵
                profile['transform'] = out_transform
                profile['height'] = first_month_data.shape[0]
                profile['width'] = first_month_data.shape[1]
                
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(R_total.astype(np.float32), 1)
                
                print(f"R因子计算完成，结果已保存至: {output_path}")
            else:
                print("无法确定输出文件的几何信息")
    else:
        print("没有找到参考tif文件")

# 使用示例
if __name__ == "__main__":
    # 设置路径
    folder_paths = [
        r"./input/坡面物源算法/R因子/2023年降雨量数据",
        r"./input/坡面物源算法/R因子/2024年降雨量数据"
    ]
    shapefile_path = r"./input/坡面物源算法/R因子/边界轮廓/边界轮廓.shp"  # 裁剪用的shp文件
    output_file = "R因子.tif"  # 输出文件路径
    
    # 执行计算 - 添加缩放因子参数
    calculate_rainfall_erosion_factor(
        folder_paths, 
        shapefile_path, 
        output_file,
        scale_factor=0.1  # 设置为0.1表示将数据除以10
    )