import numpy as np
import rasterio

def compute_slbl_with_correction(dem_data, z_max, delta_x, max_value=1e4, min_value=-1e4, max_iter=10000):
    """
    计算SLBL面，加入容差，使滑动面更接近圆形，并限制每次更新的最大变化幅度。
    
    参数：
    - dem_data: 原始DEM数据
    - z_max: 滑坡区域的最大垂直深度
    - delta_x: 单元格的分辨率（单位：米），由DEM的分辨率给定
    - tolerance: 收敛的容差
    - max_value: 最大值限制，避免出现过大的正值
    - min_value: 最小值限制，避免出现过大的负值
    - max_iter: 最大迭代次数，防止程序陷入无限循环
    """
    slbl_surface = np.copy(dem_data)  # 初始化SLBL面
    previous_slbl_surface = np.copy(dem_data)  # 存储上一轮SLBL面
    iteration = 0  # 迭代计数

    # 获取滑坡区域的行列索引
    rows, cols = np.where(dem_data > -np.inf)  # 这里使用了-∞来获取所有有效区域

    # 计算滑坡区域每一行的宽度（即每一行内滑坡区域的宽度）
    widths = []
    for r in np.unique(rows):  # 遍历每一行
        row_cols = cols[rows == r]  # 获取该行滑坡区域对应的列
        if len(row_cols) > 0:
            row_width = np.max(row_cols) - np.min(row_cols)  # 该行滑坡的宽度
            widths.append(row_width)
    
    # 计算宽度的平均值
    if widths:
        avg_width = np.mean(widths)
    else:
        avg_width = 0  # 防止滑坡区域为空

    # 计算滑坡区域每一列的长度（即每一列内滑坡区域的长度）
    lengths = []
    for c in np.unique(cols):  # 遍历每一列
        col_rows = rows[cols == c]  # 获取该列滑坡区域对应的行
        if len(col_rows) > 0:
            col_length = np.max(col_rows) - np.min(col_rows)  # 该列滑坡的长度
            lengths.append(col_length)
    
    # 计算长度的平均值
    if lengths:
        avg_length = np.mean(lengths)
    else:
        avg_length = 0  # 防止滑坡区域为空

    # 打印滑坡的平均宽度和长度
    print(f"滑坡区域的平均宽度: {avg_width*delta_x}")
    print(f"滑坡区域的平均长度: {avg_length*delta_x}")

    # 计算滑坡的几何面积 A_hs
    A_hs = ( ((avg_width*delta_x + avg_length*delta_x)/2)**2)  # 用平均值计算几何面积

    # 打印几何面积
    print(f" A_hs: {A_hs}")

    # 计算容差（C）
    C = (4 * z_max * delta_x ** 2) /( ((avg_width*delta_x + avg_length*delta_x)/2)**2)   # 容差公式

    # 打印容差的初始值
    print(f"计算得到的容差 C：{C}")

    while iteration < max_iter:
        iteration += 1

        # 计算相邻单元格的最大值和最小值
        shift_up = np.roll(slbl_surface, 1, axis=0)  # 使用 slbl_surface 计算邻域
        shift_down = np.roll(slbl_surface, -1, axis=0)
        shift_left = np.roll(slbl_surface, 1, axis=1)
        shift_right = np.roll(slbl_surface, -1, axis=1)

        # 处理边界，避免不正确的滚动
        shift_up[0, :] = slbl_surface[0, :]
        shift_down[-1, :] = slbl_surface[-1, :]
        shift_left[:, 0] = slbl_surface[:, 0]
        shift_right[:, -1] = slbl_surface[:, -1]  # 修正为: 将最后一列赋值给shift_right的最后一列

        # 计算最大值和最小值
        max_neighbors = np.maximum(np.maximum(shift_up, shift_down), np.maximum(shift_left, shift_right))
        min_neighbors = np.minimum(np.minimum(shift_up, shift_down), np.minimum(shift_left, shift_right))

        # 检测异常值：如果有`inf`或超过合理范围的值，不进行更新
        max_valid = np.where(np.isinf(max_neighbors) | (max_neighbors > max_value), False, True)
        min_valid = np.where(np.isinf(min_neighbors) | (min_neighbors < min_value), False, True)

        # 计算最大值和最小值的平均值，只在有效邻域进行计算
        avg_neighbors = (max_neighbors + min_neighbors) / 2
        avg_neighbors = np.where(max_valid & min_valid, avg_neighbors, slbl_surface)

        # 加入容差（C）：直接减去固定值，使面更弯曲
        avg_neighbors = avg_neighbors - C

        # 更新SLBL面：如果当前值大于邻域平均值，更新为邻域平均值
        slbl_surface = np.where(dem_data > avg_neighbors, avg_neighbors, slbl_surface)

        # 限制更新幅度，避免数值溢出
        slbl_surface = np.clip(slbl_surface, dem_data - max_value, dem_data + max_value)

        # 计算相邻两次迭代的变化
        change = np.abs(slbl_surface - previous_slbl_surface)

        # 忽略 NaN 值的影响：将 NaN 设置为 0 或者过滤掉 NaN
        change[np.isnan(change)] = 0  # 将 NaN 值的变化量设置为 0

        # 打印当前迭代中变化的最大值
        max_change = np.max(change)
        print(f"Iteration {iteration}, Max Change: {max_change}")

        tolerance=2*C,

        # 如果变化小于容忍度，则停止迭代
        if np.max(change) < tolerance:
            print(f"Converged after change < {tolerance}")
            break

        # 更新上一轮SLBL面
        previous_slbl_surface = np.copy(slbl_surface)

        # 处理无穷大和NaN值：替换为合理范围
        if np.any(np.isinf(slbl_surface)):
            print(f"Warning: Infinite values encountered")
            slbl_surface[np.isinf(slbl_surface)] = np.nan
        
        # 如果存在NaN或极端负值，修正为合理范围
        if np.any(slbl_surface < -1e10):  # 假设负值不合理，修正为最小值
            print(f"Warning: Large negative values detected")
            slbl_surface[slbl_surface < -1e10] = np.nan

    # 修复NaN值为DEM的原始最小值
    slbl_surface = np.nan_to_num(slbl_surface, nan=np.nanmin(dem_data))

    return slbl_surface

# 将SLBL面保存为GeoTIFF文件
def save_slbl_to_tiff(slbl_surface, output_path, reference_dem_path):
    with rasterio.open(reference_dem_path) as src:
        profile = src.profile

    try:
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(slbl_surface, 1)
        print(f"SLBL面已保存为 {output_path}")
    except Exception as e:
        print(f"Error saving SLBL file: {e}")

# 修改为main1
def main1(dem_path,max_iter=10000,output_slbl_path='calculated_slbl_with_correction.tif'):
    with rasterio.open(dem_path) as src:
        dem_data = src.read(1)  # 读取DEM的第一个波段
        
        # 获取 DEM 的分辨率（每个像素的大小）
        delta_x = src.transform[0]  # 水平方向的分辨率（单位：米）
        print(f"DEM 文件分辨率（单元格大小）：{delta_x} 米")

    z_max = 5  # 假设的滑坡最大平均深度
    slbl_surface = compute_slbl_with_correction(dem_data, z_max, delta_x,max_iter = max_iter)

    # output_slbl_path = 'calculated_slbl_with_correction.tif'
    save_slbl_to_tiff(slbl_surface, output_slbl_path, dem_path)

# 示例：替换为您自己的DEM文件路径
if __name__ == "__main__":
    dem_path = '222.tif'
    # 修改为main1
    main1(dem_path)

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from osgeo import gdal, gdalconst

# 输出文件路径
outputfilePath = 'ReprojectImage.tif'

# 输入文件路径（待重投影的影像）
inputfilePath = 'calculated_slbl_with_correction.tif'
# 参考文件路径（用于重投影的目标影像）
referencefilefilePath = '222.tif'

def save_output_image(outputrasfile, outputfilePath):
    """
    保存输出影像（已重投影的影像）到指定路径
    """
    driver = gdal.GetDriverByName('GTiff')
    if driver is None:
        print("无法获取GTiff驱动。")
        return
    output_band = outputrasfile.GetRasterBand(1)
    
    # 创建新的影像文件
    output = driver.Create(outputfilePath, outputrasfile.RasterXSize, outputrasfile.RasterYSize, 
                           outputrasfile.RasterCount, output_band.DataType)
    output.SetGeoTransform(outputrasfile.GetGeoTransform())
    output.SetProjection(outputrasfile.GetProjection())
    
    # 将数据从源影像写入输出影像
    output_band = output.GetRasterBand(1)
    data = outputrasfile.GetRasterBand(1).ReadAsArray()
    output_band.WriteArray(data)
    
    # 设置 NoData 值
    no_data_value = output_band.GetNoDataValue()
    if no_data_value is not None:
        output_band.SetNoDataValue(no_data_value)
    
    output.FlushCache()
    print(f"输出影像已保存至 {outputfilePath}")

def ReprojectImages():
    """
    进行影像重投影，目标影像的投影、地理变换和尺寸由参考影像决定。
    """
    # 获取输入影像信息
    inputrasfile = gdal.Open(inputfilePath, gdal.GA_ReadOnly)
    if inputrasfile is None:
        print("无法打开输入影像文件。")
        return
    inputProj = inputrasfile.GetProjection()

    # 获取参考影像信息
    referencefile = gdal.Open(referencefilefilePath, gdal.GA_ReadOnly)
    if referencefile is None:
        print("无法打开参考影像文件。")
        return
    referencefileProj = referencefile.GetProjection()
    referencefileTrans = referencefile.GetGeoTransform()
    bandreferencefile = referencefile.GetRasterBand(1)

    # 获取参考影像的尺寸
    Width = referencefile.RasterXSize
    Height = referencefile.RasterYSize
    nbands = referencefile.RasterCount

    # 获取输入影像的 NoData 值
    input_band = inputrasfile.GetRasterBand(1)
    input_no_data = input_band.GetNoDataValue()

    # 创建输出影像（设置投影及地理变换）
    driver = gdal.GetDriverByName('GTiff')
    if driver is None:
        print("无法获取GTiff驱动。")
        return
    output = driver.Create(outputfilePath, Width, Height, nbands, bandreferencefile.DataType)

    # 设置输出影像的投影和地理变换
    output.SetGeoTransform(referencefileTrans)
    output.SetProjection(referencefileProj)

    # 设置输出影像的 NoData 值为输入影像的 NoData 值
    output_band = output.GetRasterBand(1)
    if input_no_data is not None:
        output_band.SetNoDataValue(input_no_data)

    # 执行重投影，使用双线性插值
    gdal.ReprojectImage(inputrasfile, output, inputProj, referencefileProj, gdalconst.GRA_Bilinear, 0.0, 0.0)

    print("重投影完成！")

    # 保存输出影像
    save_output_image(output, outputfilePath)

def compute_volume_difference():
    """
    计算输出影像与参考影像之间的体积差
    """
    # 打开输出影像和参考影像
    outputrasfile = gdal.Open(outputfilePath, gdal.GA_ReadOnly)
    referencefile = gdal.Open(referencefilefilePath, gdal.GA_ReadOnly)

    # 获取输出影像和参考影像的波段
    output_band = outputrasfile.GetRasterBand(1)
    reference_band = referencefile.GetRasterBand(1)

    # 获取输出影像和参考影像的数组数据
    output_data = output_band.ReadAsArray()
    reference_data = reference_band.ReadAsArray()

    # 获取像元的大小（假设像元大小为 5m x 5m）
    pixel_size = 5.0  # 像元大小，单位：米
    area_per_pixel = pixel_size ** 2  # 像元的面积，单位：平方米

    # 计算高程差
    elevation_diff = output_data - reference_data

    # 移除 NoData 值
    output_no_data = output_band.GetNoDataValue()
    reference_no_data = reference_band.GetNoDataValue()
    if output_no_data is not None:
        elevation_diff[output_data == output_no_data] = np.nan
    if reference_no_data is not None:
        elevation_diff[reference_data == reference_no_data] = np.nan

    # 跳过 NaN 和 Inf 值的像元
    valid_mask = ~np.isnan(elevation_diff) & ~np.isinf(elevation_diff)

    # 计算每个有效像元的体积差
    valid_elevation_diff = elevation_diff[valid_mask]
    valid_volume_diff = valid_elevation_diff * area_per_pixel  # 体积，单位：立方米

    # 计算总的体积差
    total_volume_diff = abs(np.sum(valid_volume_diff))  # 忽略无效值（NaN 和 Inf）进行求和
    print(f"计算得到的体积差：{total_volume_diff} 立方米")

    return valid_mask, elevation_diff, output_data

def plot_3d_cubes_with_surface(valid_mask, elevation_diff, output_data):
    """
    在三维空间中展示 DEM 的表面和小立方体。
    """
    # 获取有效的高程差位置（跳过 NaN 和 Inf 值）
    rows, cols = np.where(valid_mask)

    # 创建立方体的三维坐标
    x = cols  # X 坐标为列索引
    y = rows  # Y 坐标为行索引
    z = output_data[valid_mask]  # Z 坐标为 DEM 高程数据

    # 每个立方体的边长为像元大小
    cube_size = 5  # 立方体边长（米）
    
    # 立方体的高度（高程差）
    heights = np.abs(elevation_diff[valid_mask])  # 使用高程差的绝对值

    # 创建一个新的图形窗口
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制 DEM 表面，透明度设置为 0.2，避免遮挡小立方体
    X, Y = np.meshgrid(np.arange(output_data.shape[1]), np.arange(output_data.shape[0]))
    ax.plot_surface(X, Y, output_data, cmap='terrain', edgecolor='k', alpha=0, linewidth=0.5)

    # 绘制每个立方体的底面和顶部
    for i in range(len(x)):
        ax.bar3d(x[i], y[i], z[i], cube_size, cube_size, heights[i], shade=True)
    
    # 设置标签
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # 显示图形
    plt.show()

# 修改为main2
def main2():
    """
    主函数，进行影像重投影、计算体积差，并进行 3D 可视化。
    """
    # 调用影像重投影函数
    ReprojectImages()

    # 计算体积差
    valid_mask, elevation_diff, output_data = compute_volume_difference()

    # 3D 可视化：绘制 DEM 和小立方体
    plot_3d_cubes_with_surface(valid_mask, elevation_diff, output_data)

# 如果是直接运行脚本，则执行 main 函数
if __name__ == "__main__":
    main2()
