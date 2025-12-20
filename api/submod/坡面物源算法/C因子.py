import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.plot import show
import geopandas as gpd
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)

def calculate_vegetation_cover_factor(ndvi_file_path, shp_file_path, output_dir="output"):
    """
    基于NDVI数据计算植被覆盖因子C
    
    参数:
    ndvi_file_path: NDVI TIF文件路径
    shp_file_path: 裁剪用的Shp文件路径
    output_dir: 输出目录
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # 读取Shp文件
        print(f"读取Shp文件: {shp_file_path}")
        gdf = gpd.read_file(shp_file_path)
        if gdf.crs is None:
            print("警告: Shp文件缺少坐标系信息，将使用NDVI文件的坐标系")
        
        # 读取NDVI数据
        print(f"读取NDVI文件: {ndvi_file_path}")
        with rasterio.open(ndvi_file_path) as src:
            # 检查坐标系是否匹配
            if gdf.crs is not None and gdf.crs != src.crs:
                print(f"坐标系不匹配: Shp文件为{gdf.crs}, NDVI文件为{src.crs}")
                print("正在转换Shp文件坐标系以匹配NDVI文件...")
                gdf = gdf.to_crs(src.crs)
            
            # 获取裁剪几何
            geometries = gdf.geometry.values
            
            # 裁剪NDVI数据
            print("裁剪NDVI数据...")
            clipped_ndvi, clipped_transform = mask(src, geometries, crop=True, nodata=np.nan)
            clipped_ndvi = clipped_ndvi[0]  # 获取第一个波段
            
            # 更新元数据
            profile = src.profile.copy()
            profile.update({
                'height': clipped_ndvi.shape[0],
                'width': clipped_ndvi.shape[1],
                'transform': clipped_transform,
                'nodata': np.nan
            })
            
            # 保存裁剪后的NDVI
            clipped_ndvi_file = os.path.join(output_dir, "裁剪后ndvi.tif")
            with rasterio.open(clipped_ndvi_file, 'w', **profile) as dst:
                dst.write(clipped_ndvi, 1)
            print(f"裁剪后的NDVI已保存为: {clipped_ndvi_file}")
            
            # 处理无效值
            clipped_ndvi = clipped_ndvi.astype(np.float32)
            if src.nodata is not None:
                clipped_ndvi[clipped_ndvi == src.nodata] = np.nan
            
            print(f"裁剪后NDVI数据形状: {clipped_ndvi.shape}")
            print(f"裁剪后NDVI有效值范围: {np.nanmin(clipped_ndvi):.4f} ~ {np.nanmax(clipped_ndvi):.4f}")
            
            # 步骤1: 计算植被覆盖度f (根据图1公式)
            # 修正后的公式: f = (NDVI - NDVI_min) / (NDVI_max - NDVI_min)
            print("正在计算植被覆盖度f...")
            with np.errstate(divide='ignore', invalid='ignore'):
                # 计算每个像素的f值
                f = (clipped_ndvi - np.nanmin(clipped_ndvi)) / (np.nanmax(clipped_ndvi) - np.nanmin(clipped_ndvi))
            
            print(f"植被覆盖度f范围: {np.nanmin(f):.4f} ~ {np.nanmax(f):.4f}")
            
            # 步骤2: 根据图2的分段函数计算植被覆盖因子C
            print("正在计算植被覆盖因子C...")
            # 初始化C数组
            C = np.full_like(f, np.nan)
            
            # 条件1: f < 0.1 时, C = 1
            mask1 = f < 0.1
            C[mask1] = 1.0
            print(f"低植被覆盖区域(f<0.1)比例: {np.sum(mask1) / np.sum(~np.isnan(f)) * 100:.2f}%")
            
            # 条件2: 0.1 <= f <= 0.783 时, C = 0.6508 - 0.3436 * lg(f)
            mask2 = (f >= 0.1) & (f <= 0.783)
            # 避免对0或负数取对数
            valid_f = f[mask2]
            valid_f[valid_f <= 0] = 1e-10  # 避免对数计算错误
            C[mask2] = 0.6508 - 0.3436 * np.log10(valid_f)
            print(f"中等植被覆盖区域(0.1≤f≤0.783)比例: {np.sum(mask2) / np.sum(~np.isnan(f)) * 100:.2f}%")
            
            # 条件3: f > 0.783 时, C = 0
            mask3 = f > 0.783
            C[mask3] = 0.0
            print(f"高植被覆盖区域(f>0.783)比例: {np.sum(mask3) / np.sum(~np.isnan(f)) * 100:.2f}%")
            
            print(f"植被覆盖因子C范围: {np.nanmin(C):.4f} ~ {np.nanmax(C):.4f}")
            
            # 保存植被覆盖度f为TIF文件
            f_output_profile = profile.copy()
            f_output_profile.update(dtype=rasterio.float32, nodata=-9999)
            
            f_output_file = os.path.join(output_dir, "植被覆盖度f.tif")
            with rasterio.open(f_output_file, 'w', **f_output_profile) as dst:
                # 将NaN值替换为nodata值
                f_data_to_save = f.copy()
                f_data_to_save[np.isnan(f_data_to_save)] = -9999
                dst.write(f_data_to_save.astype(rasterio.float32), 1)
            print(f"植被覆盖度f已保存为: {f_output_file}")
            
            # 保存植被覆盖因子C为TIF文件
            C_output_profile = profile.copy()
            C_output_profile.update(dtype=rasterio.float32, nodata=-9999)
            
            C_output_file = os.path.join(output_dir, "C因子.tif")
            with rasterio.open(C_output_file, 'w', **C_output_profile) as dst:
                # 将NaN值替换为nodata值
                C_data_to_save = C.copy()
                C_data_to_save[np.isnan(C_data_to_save)] = -9999
                dst.write(C_data_to_save.astype(rasterio.float32), 1)
            print(f"植被覆盖因子C已保存为: {C_output_file}")
            
            # 生成结果统计报告
            generate_statistics_report(clipped_ndvi, f, C, output_dir)
            
            # 可视化结果
            create_visualization(clipped_ndvi, f, C, output_dir)
            
            return C, f
            
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return None, None

def generate_statistics_report(ndvi, f, C, output_dir):
    """生成统计报告"""
    report_file = os.path.join(output_dir, "statistics_report.txt")
    
    with open(report_file, 'w') as f_report:
        f_report.write("植被覆盖因子计算统计报告\n")
        f_report.write("=" * 50 + "\n\n")
        
        f_report.write("NDVI统计:\n")
        f_report.write(f"  最小值: {np.nanmin(ndvi):.4f}\n")
        f_report.write(f"  最大值: {np.nanmax(ndvi):.4f}\n")
        f_report.write(f"  平均值: {np.nanmean(ndvi):.4f}\n")
        f_report.write(f"  标准差: {np.nanstd(ndvi):.4f}\n\n")
        
        f_report.write("植被覆盖度f统计:\n")
        f_report.write(f"  最小值: {np.nanmin(f):.4f}\n")
        f_report.write(f"  最大值: {np.nanmax(f):.4f}\n")
        f_report.write(f"  平均值: {np.nanmean(f):.4f}\n\n")
        
        f_report.write("植被覆盖因子C统计:\n")
        f_report.write(f"  最小值: {np.nanmin(C):.4f}\n")
        f_report.write(f"  最大值: {np.nanmax(C):.4f}\n")
        f_report.write(f"  平均值: {np.nanmean(C):.4f}\n\n")
        
        # 计算各分段的像素数量
        total_pixels = np.sum(~np.isnan(f))
        low_cover = np.sum(f < 0.1)
        medium_cover = np.sum((f >= 0.1) & (f <= 0.783))
        high_cover = np.sum(f > 0.783)
        
        f_report.write("植被覆盖度分布:\n")
        f_report.write(f"  f < 0.1 (低覆盖): {low_cover} 像素 ({low_cover/total_pixels*100:.2f}%)\n")
        f_report.write(f"  0.1 ≤ f ≤ 0.783 (中覆盖): {medium_cover} 像素 ({medium_cover/total_pixels*100:.2f}%)\n")
        f_report.write(f"  f > 0.783 (高覆盖): {high_cover} 像素 ({high_cover/total_pixels*100:.2f}%)\n")
    
    print(f"统计报告已保存为: {report_file}")

def create_visualization(ndvi, f, C, output_dir):
    """创建可视化图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 显示原始NDVI数据
    im1 = axes[0, 0].imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
    axes[0, 0].set_title('裁剪后NDVI数据')
    plt.colorbar(im1, ax=axes[0, 0])
    
    # 显示植被覆盖度f
    im2 = axes[0, 1].imshow(f, cmap='viridis')
    axes[0, 1].set_title('植被覆盖度f')
    plt.colorbar(im2, ax=axes[0, 1])
    
    # 显示植被覆盖因子C
    im3 = axes[1, 0].imshow(C, cmap='plasma')
    axes[1, 0].set_title('植被覆盖因子C')
    plt.colorbar(im3, ax=axes[1, 0])
    
    # 显示植被覆盖度直方图
    axes[1, 1].hist(f[~np.isnan(f)].flatten(), bins=50, alpha=0.7, color='green')
    axes[1, 1].axvline(x=0.1, color='red', linestyle='--', label='f=0.1')
    axes[1, 1].axvline(x=0.783, color='blue', linestyle='--', label='f=0.783')
    axes[1, 1].set_xlabel('植被覆盖度f')
    axes[1, 1].set_ylabel('像素数量')
    axes[1, 1].set_title('植被覆盖度分布直方图')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    visualization_file = os.path.join(output_dir, 'vegetation_analysis_results.png')
    plt.savefig(visualization_file, dpi=300, bbox_inches='tight')
    print(f"分析结果图表已保存为: {visualization_file}")
    plt.close()

# 使用示例
if __name__ == "__main__":
    # 请将这里的文件路径替换为您的实际文件路径
    ndvi_file = r"./input/坡面物源算法/c/NDVI_yearly_mean_2024.tif"
    shp_file = r"./input/坡面物源算法/c/边界轮廓/边界轮廓.shp"  # 替换为您的Shp文件路径
    
    if os.path.exists(ndvi_file) and os.path.exists(shp_file):
        print("开始计算植被覆盖因子...")
        C, f = calculate_vegetation_cover_factor(ndvi_file, shp_file)
        if C is not None:
            print("计算完成！")
        else:
            print("计算失败，请检查输入文件。")
    else:
        if not os.path.exists(ndvi_file):
            print(f"NDVI文件 {ndvi_file} 不存在")
        if not os.path.exists(shp_file):
            print(f"Shp文件 {shp_file} 不存在")
        print("请提供正确的文件路径。")