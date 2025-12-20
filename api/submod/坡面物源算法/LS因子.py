import numpy as np
import rasterio
from rasterio.windows import Window
import math
import os
from collections import deque
import time
import traceback
from tqdm import tqdm
from osgeo import gdal
import tempfile

def resample_dem_gdal(input_path, target_resolution, resampling_method='average'):
    """
    使用GDAL重采样DEM到指定分辨率
    
    参数:
    input_path: 输入的DEM文件路径
    target_resolution: 目标分辨率(米)
    resampling_method: 重采样方法，默认为average
    
    返回:
    重采样后的临时文件路径
    """
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.tif', delete=False).name
    
    # 打开原始DEM
    ds_orig = gdal.Open(input_path)
    transform_orig = ds_orig.GetGeoTransform()
    orig_pixel_size = transform_orig[1]
    
    # 计算新的行列数
    x_size = ds_orig.RasterXSize
    y_size = ds_orig.RasterYSize
    new_x_size = int(x_size * orig_pixel_size / target_resolution)
    new_y_size = int(y_size * orig_pixel_size / target_resolution)
    
    # 重采样选项
    resample_alg = {
        'average': gdal.GRA_Average,
        'bilinear': gdal.GRA_Bilinear,
        'cubic': gdal.GRA_Cubic
    }.get(resampling_method.lower(), gdal.GRA_Average)
    
    # 执行重采样 in Warp return wrapper_GDALWarpDestName(destNameOrDestDS, srcDSTab, opts, callback, callback_data) File ", line 9374, in wrapper_GDALWarpDestName return _gdal.wrapper_GDALWarpDestName(*args) TypeError: in method 'wrapper_GDALWarpDestName', argument 4 of type 'GDALWarpAppOptions *'
    gdal.Warp(temp_file, ds_orig, 
              format='GTiff',
              width=new_x_size, 
              height=new_y_size,
              resampleAlg=resample_alg,
              options=['COMPRESS=LZW', 'BIGTIFF=YES'])
    
    # 清理资源
    ds_orig = None
    
    return temp_file

def calculate_slope_degrees(dem_chunk, cell_size):
    """计算坡度(度)"""
    try:
        dy, dx = np.gradient(dem_chunk, cell_size)
        slope_radians = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_degrees = np.degrees(slope_radians)
        return slope_degrees
    except Exception as e:
        return np.zeros_like(dem_chunk)

def calculate_beta(sin_theta):
    """计算β值"""
    with np.errstate(divide='ignore', invalid='ignore'):
        numerator = sin_theta / 0.0896
        denominator = 3 * (sin_theta ** 0.8) + 0.56
        beta = numerator / denominator
        beta = np.where(np.isinf(beta) | np.isnan(beta), 0, beta)
    return beta

def calculate_m(beta):
    """计算坡长指数m"""
    with np.errstate(divide='ignore', invalid='ignore'):
        m = beta / (beta + 1)
        m = np.where(np.isinf(m) | np.isnan(m), 0, m)
    return m

def calculate_s_factor(slope_degrees, sin_theta):
    """计算坡度因子S"""
    s_factor = np.zeros_like(slope_degrees)
    
    # 根据坡度分段计算S
    mask1 = slope_degrees < 5
    mask2 = (slope_degrees >= 5) & (slope_degrees < 10)
    mask3 = slope_degrees >= 10
    
    s_factor[mask1] = 10.8 * sin_theta[mask1] + 0.036
    s_factor[mask2] = 16.8 * sin_theta[mask2] - 0.50
    s_factor[mask3] = 21.9 * sin_theta[mask3] - 0.96
    
    # 确保S因子不为负
    s_factor = np.where(s_factor < 0, 0, s_factor)
    
    return s_factor

def calculate_flow_direction(dem_chunk):
    """计算流向矩阵(D8算法)"""
    height, width = dem_chunk.shape
    flow_dir = np.zeros((height, width), dtype=np.int8)
    
    # D8方向编码 (3x3邻域)
    # 5  6  7
    # 4  X  0
    # 3  2  1
    dir_dx = [1, 1, 0, -1, -1, -1, 0, 1]
    dir_dy = [0, -1, -1, -1, 0, 1, 1, 1]
    
    for i in range(height):
        for j in range(width):
            if np.isnan(dem_chunk[i, j]):
                flow_dir[i, j] = -1  # NoData
                continue
            
            max_slope = -float('inf')
            best_dir = -1
            
            for d in range(8):
                ni = i + dir_dy[d]
                nj = j + dir_dx[d]
                
                if 0 <= ni < height and 0 <= nj < width:
                    if not np.isnan(dem_chunk[ni, nj]):
                        drop = dem_chunk[i, j] - dem_chunk[ni, nj]
                        distance = math.sqrt(dir_dx[d]**2 + dir_dy[d]**2)
                        slope = drop / distance if distance > 0 else 0
                        
                        if slope > max_slope:
                            max_slope = slope
                            best_dir = d
            
            flow_dir[i, j] = best_dir if max_slope > 0 else -1
    
    return flow_dir

def calculate_flow_accumulation(dem_chunk, flow_dir):
    """计算流量累积量(D8算法)"""
    height, width = dem_chunk.shape
    flow_acc = np.ones((height, width), dtype=np.float32)
    
    # 创建依赖关系图
    dependencies = {}
    for i in range(height):
        for j in range(width):
            if flow_dir[i, j] == -1:  # 边界或平地
                continue
            
            # 根据流向确定下游像元
            d = flow_dir[i, j]
            di = i + [0, -1, -1, -1, 0, 1, 1, 1][d]
            dj = j + [1, 1, 0, -1, -1, -1, 0, 1][d]
            
            if 0 <= di < height and 0 <= dj < width:
                if (di, dj) not in dependencies:
                    dependencies[(di, dj)] = []
                dependencies[(di, dj)].append((i, j))
    
    # 拓扑排序（从源头开始）
    queue = deque()
    for i in range(height):
        for j in range(width):
            if flow_dir[i, j] != -1 and (i, j) not in dependencies:
                queue.append((i, j))
    
    # 处理队列
    while queue:
        i, j = queue.popleft()
        
        # 计算当前像元的流量累积量
        if (i, j) in dependencies:
            for up_i, up_j in dependencies[(i, j)]:
                flow_acc[i, j] += flow_acc[up_i, up_j]
        
        # 找到下游像元
        if flow_dir[i, j] != -1:
            d = flow_dir[i, j]
            di = i + [0, -1, -1, -1, 0, 1, 1, 1][d]
            dj = j + [1, 1, 0, -1, -1, -1, 0, 1][d]
            
            if 0 <= di < height and 0 <= dj < width:
                # 减少下游像元的依赖计数
                if (di, dj) in dependencies:
                    dependencies[(di, dj)] = [dep for dep in dependencies[(di, dj)] if dep != (i, j)]
                    if not dependencies[(di, dj)]:
                        queue.append((di, dj))
    
    return flow_acc

def calculate_ls_factor(dem_file, output_file, cell_size=0.1, chunk_size=500, 
                        target_resolution=None, resample_method='average'):
    """
    计算坡度坡长因子(LS)，使用分块处理大型DEM文件
    
    参数:
    dem_file: 输入的DEM文件路径
    output_file: 输出的LS因子文件路径
    cell_size: 原始像元大小(米)
    chunk_size: 分块大小（像元数），默认500x500
    target_resolution: 目标重采样分辨率(米)，如果提供则进行重采样
    resample_method: 重采样方法，默认为'average'
    """
    
    # 创建日志文件
    log_file = os.path.splitext(output_file)[0] + "_log.txt"
    with open(log_file, "w") as log:
        log.write(f"LS因子计算日志 - 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"输入DEM: {dem_file}\n")
        log.write(f"输出文件: {output_file}\n")
        log.write(f"原始像元大小: {cell_size}米\n")
        if target_resolution:
            log.write(f"目标分辨率: {target_resolution}米\n")
            log.write(f"重采样方法: {resample_method}\n")
        log.write(f"分块大小: {chunk_size}x{chunk_size}\n")
    
    def log_message(message):
        """记录日志消息"""
        print(message)
        with open(log_file, "a") as log:
            log.write(f"{time.strftime('%H:%M:%S')} - {message}\n")
    
    try:
        # 如果需要重采样，先进行重采样
        temp_resampled_file = None
        if target_resolution and target_resolution != cell_size:
            log_message(f"开始重采样至 {target_resolution} 米分辨率...")
            temp_resampled_file = resample_dem_gdal(dem_file, target_resolution, resample_method)
            dem_file = temp_resampled_file
            cell_size = target_resolution
            log_message(f"重采样完成，临时文件: {temp_resampled_file}")
        
        # 打开DEM文件
        with rasterio.open(dem_file) as src:
            # 获取DEM信息
            height = src.height
            width = src.width
            profile = src.profile
            nodata = src.nodata
            transform = src.transform
            
            log_message(f"处理尺寸: {width}x{height}")
            log_message(f"像元大小: {cell_size}米")
            log_message(f"分块大小: {chunk_size}x{chunk_size}")
            
            # 计算分块数量
            num_chunks_x = (width + chunk_size - 1) // chunk_size
            num_chunks_y = (height + chunk_size - 1) // chunk_size
            total_chunks = num_chunks_x * num_chunks_y
            
            log_message(f"分块处理: {num_chunks_x}x{num_chunks_y} 块")
            
            # 更新输出文件的元数据
            profile.update({
                'dtype': 'float32',
                'nodata': -9999,
                'driver': 'GTiff',
                'count': 1,
                'compress': 'lzw',
                'tiled': True,
                'blockxsize': min(256, chunk_size),
                'blockysize': min(256, chunk_size),
                'width': width,
                'height': height,
                'transform': transform
            })
            
            # 创建输出文件
            with rasterio.open(output_file, 'w', **profile) as dst:
                # 创建进度条
                pbar = tqdm(total=total_chunks, desc="处理分块", unit="块")
                
                # 处理每个分块
                for i in range(num_chunks_y):
                    for j in range(num_chunks_x):
                        # 计算当前块的窗口
                        yoff = i * chunk_size
                        xoff = j * chunk_size
                        win_height = min(chunk_size, height - yoff)
                        win_width = min(chunk_size, width - xoff)
                        
                        window = Window(xoff, yoff, win_width, win_height)
                        
                        try:
                            # 读取当前块的DEM数据
                            dem_chunk = src.read(1, window=window)
                            
                            # 将NoData值转换为NaN
                            if nodata is not None:
                                dem_chunk = dem_chunk.astype(np.float32)
                                dem_chunk[dem_chunk == nodata] = np.nan
                            
                            # 如果整个块都是NoData，则跳过计算
                            if np.all(np.isnan(dem_chunk)):
                                ls_chunk = np.full((win_height, win_width), -9999, dtype=np.float32)
                            else:
                                # 计算流向
                                flow_dir = calculate_flow_direction(dem_chunk)
                                
                                # 计算流量累积量
                                flow_acc = calculate_flow_accumulation(dem_chunk, flow_dir)
                                
                                # 计算坡度(度)
                                slope_degrees = calculate_slope_degrees(dem_chunk, cell_size)
                                
                                # 计算sinθ
                                slope_radians = np.radians(slope_degrees)
                                sin_theta = np.sin(slope_radians)
                                
                                # 计算β
                                beta = calculate_beta(sin_theta)
                                
                                # 计算m
                                m = calculate_m(beta)
                                
                                # 计算坡度因子S
                                s_factor = calculate_s_factor(slope_degrees, sin_theta)
                                
                                # 计算坡长λ (单位:米)
                                # λ = sqrt(流量累积量) * 像元大小
                                lambda_val = np.sqrt(flow_acc) * cell_size
                                
                                # 计算坡长因子L
                                with np.errstate(divide='ignore', invalid='ignore'):
                                    l_factor = (lambda_val / 22.1) ** m
                                    l_factor = np.where(np.isinf(l_factor) | np.isnan(l_factor), 0, l_factor)
                                
                                # 计算LS因子
                                ls_chunk = l_factor * s_factor
                                
                                # 处理异常值
                                ls_chunk = np.where(np.isinf(ls_chunk) | np.isnan(ls_chunk), 0, ls_chunk)
                                ls_chunk = np.where(ls_chunk < 0, 0, ls_chunk)
                            
                            # 将结果写入输出文件
                            dst.write(ls_chunk.astype(np.float32), 1, window=window)
                            
                            # 更新进度条
                            pbar.update(1)
                            
                        except Exception as e:
                            # 记录错误信息
                            error_msg = f"处理块 [{i},{j}] 时出错: {str(e)}"
                            log_message(error_msg)
                            log_message(traceback.format_exc())
                            
                            # 写入错误块（全为-9999）
                            error_chunk = np.full((win_height, win_width), -9999, dtype=np.float32)
                            dst.write(error_chunk.astype(np.float32), 1, window=window)
                            
                            # 更新进度条
                            pbar.update(1)
                
                # 关闭进度条
                pbar.close()
        
        log_message("\n处理完成!")
        
        # 删除临时重采样文件
        if temp_resampled_file and os.path.exists(temp_resampled_file):
            try:
                os.remove(temp_resampled_file)
                log_message(f"已删除临时文件: {temp_resampled_file}")
            except Exception as e:
                log_message(f"删除临时文件失败: {str(e)}")
        
        return output_file
    
    except Exception as e:
        log_message(f"处理过程中发生严重错误: {str(e)}")
        log_message(traceback.format_exc())
        return None

# 使用示例
if __name__ == "__main__":
    # 输入DEM文件路径和输出文件路径
    dem_path = r"./input/坡面物源算法/LS因子/c2020年核心区DEM5m_Clip1_Clip21.tif"
    output_path = "LS因子.tif"
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 询问用户是否要重采样
    resample_option = input("是否要重采样DEM? (y/n): ").strip().lower()
    target_res = None
    resample_method = 'average'
    
    if resample_option == 'y':
        try:
            target_res = float(input("请输入目标分辨率(米): "))
            resample_method = input("请输入重采样方法 (average/bilinear/cubic, 默认为average): ").strip().lower()
            if resample_method not in ['average', 'bilinear', 'cubic']:
                resample_method = 'average'
            print(f"将在 {target_res} 米分辨率下计算LS因子，使用 {resample_method} 方法")
        except ValueError:
            print("输入无效，将使用原始分辨率计算")
    
    # 计算LS因子（使用分块处理）
    result_file = calculate_ls_factor(dem_path, output_path, 
                                     chunk_size=500, 
                                     target_resolution=target_res,
                                     resample_method=resample_method)
    
    if result_file:
        print(f"LS因子计算完成，结果已保存至: {result_file}")
    else:
        print("处理失败，请检查日志文件")