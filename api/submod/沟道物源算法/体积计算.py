import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from osgeo import gdal, gdalconst

# 输出文件路径
outputfilePath = 'ReprojectImage.tif'

# 输入文件路径（待重投影的影像）
inputfilePath = 'clipped_dem_square_pixel.tif'

# 参考文件路径（用于重投影的目标影像）
referencefilefilePath = r"F:\名人堂\许英杰项目\泥石流物源体积计算\九寨沟数据\剖面线2数据测试\c2020年核心区DEM5m_Clip1_Clip21.tif"

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
    total_volume_diff = np.sum(valid_volume_diff)  # 忽略无效值（NaN 和 Inf）进行求和
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
    cube_size = 5.0  # 立方体边长（米）
    
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


def main():
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
    main()
