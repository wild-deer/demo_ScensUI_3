import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import rasterio
from pyproj import Transformer
import tempfile
from fastkml import kml
from pygeoif import geometry
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, LineString
import re
import shutil
import os
import shapefile
import pandas as pd
from scipy import interpolate
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号
# 定义坐标系和创建转换器
wgs84 = "EPSG:4326"  # WGS84
cgcs2000 = "EPSG:4544"  # CGCS2000
transformer = Transformer.from_crs(wgs84, cgcs2000, always_xy=True)

# 打开DEM文件并读取坐标信息
原始DEM = r"C:\Users\jerem\Desktop\Project\jd\课题页面\demo_scensUI_3\api\input\沟道物源\c2020年核心区DEM5m_Clip1.tif"

# 读取kml文件
剖面线kml = r"C:\Users\jerem\Desktop\Project\jd\课题页面\demo_scensUI_3\api\input\沟道物源\SL194827.kml"
边界kml_path = r"C:\Users\jerem\Desktop\Project\jd\课题页面\demo_scensUI_3\api\input\沟道物源\GD02.kml"

# 读取 KML 并处理
try:
    # 2. 使用 fastkml 读取
    k = kml.KML()
    with open(边界kml_path, 'rb') as f:
        k.from_string(f.read())

    # 3. 递归提取几何体并转换为 Shapely 对象
    def extract_geometries(features):
        geoms = []
        for feature in features:
            # A. 如果是文件夹，递归提取
            if isinstance(feature, (kml.Folder, kml.Document)):
                geoms.extend(extract_geometries(feature.features()))
            
            # B. 如果是具体的要素 (Placemark)
            elif hasattr(feature, 'geometry') and feature.geometry is not None:
                geom = feature.geometry
                coords = []

                # --- 核心修复：根据几何类型获取坐标 ---
                try:
                    # 情况 1: 如果是 Polygon (多边形)，坐标在 exterior (外环) 里
                    # 注意：fastkml/pygeoif 的 Polygon 对象没有直接的 .coords
                    if hasattr(geom, 'exterior') and geom.exterior is not None:
                        coords = list(geom.exterior.coords)
                    
                    # 情况 2: 如果是 LineString (线) 或 Point (点)，直接有 .coords
                    elif hasattr(geom, 'coords'):
                        coords = list(geom.coords)
                    
                    # 其他情况无法处理则跳过
                    else:
                        continue

                except Exception as ex:
                    print(f"警告: 跳过一个无法解析几何类型的要素 - {ex}")
                    continue

                if not coords:
                    continue
                
                # --- 转换为 Shapely 对象 ---
                # 提取 (x, y)，忽略 z
                xy_coords = [(c[0], c[1]) for c in coords]
                
                # 只有 >= 3 个点才能构成面
                if len(xy_coords) >= 3:
                    geoms.append(Polygon(xy_coords))
        
        return geoms

    shapely_polys = extract_geometries(list(k.features()))

    if not shapely_polys:
        raise ValueError("未在 KML 中提取到有效的多边形几何体")

    # 4. 创建 GeoDataFrame (指定原始坐标系 WGS84)
    gdf = gpd.GeoDataFrame(geometry=shapely_polys, crs="EPSG:4326")

    # 5. 坐标转换 (WGS84 -> CGCS2000)
    # 您的 DEM 是 EPSG:4544
    gdf = gdf.to_crs("EPSG:4544")

    # 6. 保存为临时 SHP
    temp_dir = tempfile.mkdtemp()
    temp_shp_path = os.path.join(temp_dir, "temp_boundary.shp")
    
    gdf.to_file(temp_shp_path, driver='ESRI Shapefile', encoding='utf-8')
    
    # 赋值给您的核心变量
    面shp = temp_shp_path
    
    print(f"✅ KML 转换成功 (临时路径): {temp_shp_path}")

except Exception as e:
    print(f"❌ KML 转换失败: {e}")
    # 抛出异常以停止后续错误
    raise e


#DEM裁剪
import os
import rasterio
from rasterio.mask import mask
import shapefile  # <--- 换用这个库，它非常稳定
import numpy as np

def clip_raster_by_shp(raster_path, shp_path, custom_name="clip_original"):
    print(f"--- 开始执行裁剪 ---")
    print(f"输入 DEM: {raster_path}")
    print(f"裁剪边界: {shp_path}")
    
    final_output_path = None

    # 1. 读取 SHP 几何体 (Safe Mode)
    try:
        sf = shapefile.Reader(shp_path)
        geoms = []
        for shape_rec in sf.shapeRecords():
            geoms.append(shape_rec.shape.__geo_interface__)
        print(f"✅ SHP 读取成功，包含 {len(geoms)} 个几何要素")
    except Exception as e:
        print(f"❌ SHP 读取失败: {e}")
        return None

    # 2. 执行裁剪
    try:
        with rasterio.open(raster_path) as src:
            # 尝试 mask 裁剪
            try:
                out_image, out_transform = mask(src, geoms, crop=True, nodata=0)
            except ValueError:
                print("❌ 裁剪失败：SHP 与 DEM 无重叠区域！")
                return None

            # 检查是否为空
            if np.all(out_image == 0):
                print("⚠️ 警告：裁剪结果全为 0")

            # 构建输出文件名
            # 这里简化逻辑，直接用 custom_name 防止字段读取出错
            filename = f"{custom_name}.tif"
            final_output_path = os.path.join(os.path.dirname(raster_path), filename)

            # 更新元数据
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": 0
            })

            # 写入文件
            with rasterio.open(final_output_path, "w", **out_meta) as dest:
                dest.write(out_image)
            
            print(f"✅ 裁剪文件已生成: {final_output_path}")

    except Exception as e:
        print(f"❌ 裁剪过程出错: {e}")
        return None

    # 【核心修复】：必须把路径 return 出去，否则外面接收到的是 None
    return final_output_path

# -------------------------- 执行逻辑 --------------------------

# 1. 执行裁剪，并把结果赋值给 outtif_裁剪
# 注意：这里传入的是 output_dem (插值生成的图) 和 面shp (你的GD02.shp)
DEM = clip_raster_by_shp(原始DEM, 面shp)
with rasterio.open(DEM) as dem:
    transform = dem.transform
    elevation = dem.read(1)
    nodata = dem.nodatavals[0]

# 读取KML文件
kml_file = kml.KML()
with open(剖面线kml, 'rb') as f:
    kml_file.from_string(f.read())

# 提取并转换KML中所有折线段的坐标，分组存储
line_groups = []
features = list(kml_file.features())
for feature in features:
    for placemark in feature.features():
        if isinstance(placemark.geometry, geometry.LineString):
            line_coords = []
            for lon, lat, *extra in placemark.geometry.coords:
                x, y = transformer.transform(lon, lat)
                ele = extra[0] if extra else 0
                line_coords.append((x, y, ele))
            line_groups.append(line_coords)

# 对每组线段坐标执行匹配检查并找到最外侧点
match_groups = []
outermost_groups = []
features = list(kml_file.features())
for feature in features:
    for placemark in feature.features():
        if isinstance(placemark.geometry, geometry.LineString):
            line_coords = []
            for lon, lat, *extra in placemark.geometry.coords:
                x, y = transformer.transform(lon, lat)
                col, row = ~transform * (x, y)
                if 0 <= row < elevation.shape[0] and 0 <= col < elevation.shape[1]:
                    ele = elevation[int(row), int(col)]
                    if ele != nodata:
                        line_coords.append((x, y, ele))
            if line_coords:
                match_groups.append(line_coords)
                coords_array = np.array(line_coords)
                center = np.mean(coords_array[:, :2], axis=0)
                distances = np.linalg.norm(coords_array[:, :2] - center, axis=1)
                max_dist_idx = distances.argsort()[-2:]
                # 添加判断防止重复
                if max_dist_idx[0] == max_dist_idx[1]:
                    second_max_idx = distances.argsort()[-3]
                    max_dist_idx = [max_dist_idx[0], second_max_idx]
                outermost_groups.append(coords_array[max_dist_idx])

# 过滤每组中X1与X2之间的点
filtered_groups = []
for line_coords, outermost_points in zip(line_groups, outermost_groups):
    if len(outermost_points) < 2:
        filtered_groups.append(line_coords)
        continue
    outermost_indices = [np.argmin(np.linalg.norm(np.array(line_coords)[:, :2] - point[:2], axis=1)) for point in outermost_points]
    min_idx, max_idx = sorted(outermost_indices)
    filtered_group = line_coords[:min_idx] + line_coords[max_idx+1:]
    filtered_groups.append(filtered_group)

def fit_line_3d(points):
    points = np.asarray(points)
    center = points.mean(axis=0)
    centered_points = points - center
    U, S, Vt = np.linalg.svd(centered_points)
    direction = Vt[0]
    return center, direction

def process_group(line_coords, outermost_points):
    if len(outermost_points) < 2:
        return None, None, None, None, None, line_coords

    outermost_indices = [np.argmin(np.linalg.norm(np.array(line_coords)[:, :2] - point[:2], axis=1)) for point in outermost_points]
    min_idx, max_idx = sorted(outermost_indices)
    filtered_group = line_coords[:min_idx] + line_coords[max_idx+1:]

    x1, x2 = outermost_points
    x1_side = [point for point in filtered_group if np.linalg.norm(np.array(point[:2]) - np.array(x1[:2])) < np.linalg.norm(np.array(point[:2]) - np.array(x2[:2]))]
    x2_side = [point for point in filtered_group if np.linalg.norm(np.array(point[:2]) - np.array(x2[:2])) < np.linalg.norm(np.array(point[:2]) - np.array(x1[:2]))]

    center1, direction1 = fit_line_3d(x1_side)
    center2, direction2 = fit_line_3d(x2_side)
    intersection_point, _ = line_intersection(center1, direction1, center2, direction2)

    return center1, direction1, center2, direction2, intersection_point, filtered_group

def line_intersection(center1, direction1, center2, direction2):
    A = np.array([direction1, -direction2]).T
    b = center2 - center1
    t = np.linalg.lstsq(A, b, rcond=None)[0]
    point_on_line1 = center1 + t[0] * direction1
    point_on_line2 = center2 + t[1] * direction2
    return (point_on_line1 + point_on_line2) / 2, np.linalg.norm(point_on_line1 - point_on_line2)

# 配置颜色
line_colors = plt.cm.viridis(np.linspace(0, 1, len(line_groups)))
point_colors = plt.cm.spring(np.linspace(0, 1, len(line_groups)))

# 可视化
fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
for idx, (line_coords, outermost_points) in enumerate(zip(line_groups, outermost_groups)):
    center1, direction1, center2, direction2, intersection_point, filtered_group = process_group(line_coords, outermost_points)
    if center1 is not None and center2 is not None:
        # 绘制原始点坐标
        xs, ys, zs = zip(*filtered_group)
        ax.scatter(xs, ys, zs, color=line_colors[idx], label=f'Group {idx+1} Points', s=20)
        
        # 绘制拟合的直线
        line1_points = center1 + np.outer(np.linspace(-100, 100, 1000), direction1)
        line2_points = center2 + np.outer(np.linspace(-100, 100, 1000), direction2)
        ax.plot(line1_points[:, 0], line1_points[:, 1], line1_points[:, 2], color=line_colors[idx])
        ax.plot(line2_points[:, 0], line2_points[:, 1], line2_points[:, 2], color=line_colors[idx])
        
        if intersection_point is not None:
            ax.scatter(*intersection_point, color=point_colors[idx], s=100, label=f'Intersection {idx+1}')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.legend()
plt.show()

import csv

# 保存每组的X1, X2, X3坐标
coordinates_data = []

for idx, (line_coords, outermost_points) in enumerate(zip(line_groups, outermost_groups)):
    # 使用已经定义的函数计算每组的处理结果
    center1, direction1, center2, direction2, intersection_point, filtered_group = process_group(line_coords, outermost_points)
    
    # 如果存在交点，则保存结果
    if center1 is not None and center2 is not None:
        coordinates_data.append({
            "Group": idx + 1,
            "X1": outermost_points[0],
            "X2": outermost_points[1],
            "X3": intersection_point
        })

# 写入CSV文件
with open("每组X1_X2_X3坐标点.csv", "w", newline='') as file:
    fieldnames = ['Group', 'X1 (X, Y, Z)', 'X2 (X, Y, Z)', 'X3 (X, Y, Z)']
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()
    for data in coordinates_data:
        x1_formatted = f"({data['X1'][0]:.5f}, {data['X1'][1]:.5f}, {data['X1'][2]:.5f})"
        x2_formatted = f"({data['X2'][0]:.5f}, {data['X2'][1]:.5f}, {data['X2'][2]:.5f})"
        x3_formatted = f"({data['X3'][0]:.5f}, {data['X3'][1]:.5f}, {data['X3'][2]:.5f})"
        writer.writerow({
            'Group': data['Group'],
            'X1 (X, Y, Z)': x1_formatted,
            'X2 (X, Y, Z)': x2_formatted,
            'X3 (X, Y, Z)': x3_formatted
        })

print("坐标数据已成功保存到 '每组X1_X2_X3坐标点.csv'")

# 读取CSV文件
data = pd.read_csv("每组X1_X2_X3坐标点.csv")

# 定义函数，用于从字符串解析坐标 (x, y, z)
def parse_coordinates(coord_str):
    match = re.match(r'\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)', coord_str)
    if match:
        return float(match.group(1)), float(match.group(2)), float(match.group(3))
    raise ValueError(f"无法解析坐标: {coord_str}")

# 计算三角形的内心
def calculate_incenter(x1, y1, z1, x2, y2, z2, x3, y3, z3):
    a = np.linalg.norm([x2 - x3, y2 - y3, z2 - z3])
    b = np.linalg.norm([x3 - x1, y3 - y1, z3 - z1])
    c = np.linalg.norm([x1 - x2, y1 - y2, z1 - z2])
    return (a * x1 + b * x2 + c * x3) / (a + b + c), (a * y1 + b * y2 + c * y3) / (a + b + c), (a * z1 + b * z2 + c * z3) / (a + b + c)

# 计算 B-spline 曲线
def calculate_bspline_curve(x, y, z):
    tck_x = interpolate.splrep([0, 1, 2], x, k=2)
    tck_y = interpolate.splrep([0, 1, 2], y, k=2)
    tck_z = interpolate.splrep([0, 1, 2], z, k=2)
    u_new = np.linspace(0, 2, 100)
    return interpolate.splev(u_new, tck_x), interpolate.splev(u_new, tck_y), interpolate.splev(u_new, tck_z)

# 存储所有曲线的坐标和用于可视化的数据
all_curves_data = pd.DataFrame()
triangle_points = []
bspline_curves = []

for idx, row in data.iterrows():
    p1 = parse_coordinates(row['X1 (X, Y, Z)'])
    p2 = parse_coordinates(row['X2 (X, Y, Z)'])
    p3 = parse_coordinates(row['X3 (X, Y, Z)'])
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    x3, y3, z3 = p3
    x0, y0, z0 = calculate_incenter(x1, y1, z1, x2, y2, z2, x3, y3, z3)
    x = [x1, x0, x2]
    y = [y1, y0, y2]
    z = [z1, z0, z2]
    x_new, y_new, z_new = calculate_bspline_curve(x, y, z)
    curve_data = pd.DataFrame({'X': x_new, 'Y': y_new, 'Z': z_new})
    all_curves_data = pd.concat([all_curves_data, curve_data], ignore_index=True)
    triangle_points.append((x, y, z))
    bspline_curves.append((x_new, y_new, z_new))

# 保存为CSV文件
all_curves_data.to_csv("B样条点坐标.csv", index=False)

# 可视化
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
colors = plt.cm.viridis(np.linspace(0, 1, len(data)))

for (x, y, z), (x_new, y_new, z_new), color in zip(triangle_points, bspline_curves, colors):
    ax.scatter(x, y, z, color=color, s=50)
    ax.plot(x_new, y_new, z_new, color=color)

ax.set_xlabel('X Coordinate')
ax.set_ylabel('Y Coordinate')
ax.set_zlabel('Z Coordinate')
plt.show()

# 1. 读取 KML
boundary_kml = kml.KML()
try:
    with open(边界kml_path, 'rb') as f:
        boundary_kml.from_string(f.read())
    print(f"成功读取 KML 文件: {边界kml_path}")
except Exception as e:
    print(f"读取 KML 文件失败: {e}")
    exit() # 或者做其他错误处理

# 3. 定义提取坐标的列表
boundary_coordinates = []

# 定义递归函数以处理 KML 可能存在的文件夹嵌套结构 (Folder/Document)
def extract_kml_coords(features_list):
    for feature in features_list:
        # 如果是文件夹或文档，递归进入
        if isinstance(feature, (kml.Folder, kml.Document)):
            extract_kml_coords(feature.features())
        # 如果是包含几何信息的要素 (Placemark)
        elif hasattr(feature, 'geometry') and feature.geometry is not None:
            geom = feature.geometry
            coords_to_process = []
            
            # 根据几何类型获取坐标点列表
            if isinstance(geom, geometry.Point):
                # Point 的 coords 通常是一个包含单个元组的列表 [(lon, lat, z)]
                coords_to_process = geom.coords
            elif isinstance(geom, (geometry.LineString, geometry.LinearRing)):
                coords_to_process = geom.coords
            elif isinstance(geom, geometry.Polygon):
                # 多边形取外环坐标
                coords_to_process = geom.exterior.coords
            
            # 遍历该要素的所有坐标点进行投影转换
            for coord in coords_to_process:
                lon, lat = coord[0], coord[1]
                # 获取高程 Z (如果 KML 里没有高程，默认为 0)
                ele = coord[2] if len(coord) > 2 else 0
                
                # 投影转换 (WGS84 -> CGCS2000)
                # 注意：transformer 变量需在上下文前面已定义 (即 Code A 前半部分)
                x, y = transformer.transform(lon, lat)
                
                boundary_coordinates.append((x, y, ele))

# 4. 执行提取
extract_kml_coords(list(boundary_kml.features()))

# 5. 保存为 CSV
if boundary_coordinates:
    coordinates_df = pd.DataFrame(boundary_coordinates, columns=['X', 'Y', 'Z'])
    coordinates_df.to_csv("DEM边界点坐标.csv", index=False)
    print(f"已提取 {len(boundary_coordinates)} 个坐标点，并保存至 'DEM边界点坐标.csv'")
else:
    print("警告：未在 KML 文件中提取到任何坐标信息，请检查文件内容。")

# 读取两个 CSV 文件
bspline_points_df = pd.read_csv("B样条点坐标.csv")
dem_boundary_points_df = pd.read_csv("DEM边界点坐标.csv")

# 按行合并（叠加坐标点）
merged_df = pd.concat([bspline_points_df, dem_boundary_points_df], ignore_index=True)

# 保存合并后的数据
merged_df.to_csv("拟合点坐标.csv", index=False)
print("两个 CSV 文件已合并并保存为 '拟合点坐标.csv'")

import numpy as np
import pandas as pd
from scipy import interpolate
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS
import matplotlib.pyplot as plt

# 读取CSV文件（包含 X, Y, Z 坐标）
df = pd.read_csv("拟合点坐标.csv")  # 替换为你的CSV文件路径
X = df['X'].values
Y = df['Y'].values
Z = df['Z'].values

# 使用二维插值（例如：基于线性插值或样条插值）
# 创建一个网格，用于插值生成更多的点
grid_x, grid_y = np.meshgrid(np.linspace(min(X), max(X), 100), 
                             np.linspace(min(Y), max(Y), 100))

# 使用 'griddata' 进行插值
# method 可以选择 ['linear', 'nearest', 'cubic']（线性插值、最邻近插值、样条插值）
grid_z = interpolate.griddata((X, Y), Z, (grid_x, grid_y), method='linear')

# 可视化插值结果
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
#ax.scatter(X, Y, Z, color='red', label='原始数据')
ax.plot_surface(grid_x, grid_y, grid_z, cmap='jet', alpha=0.7)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('插值生成 DEM')
ax.legend()
plt.show()

# 将插值结果保存为 DEM（GeoTIFF 格式）
# 直接反转 Y 坐标：让 Y 坐标从大到小，以适应 DEM 格式
grid_z_flipped = np.flip(grid_z, axis=0)  # 反转 Z 数据以匹配反转的 Y 坐标

# 创建 rasterio 的 transform 和 metadata
# 反转 Y 轴：在 GeoTIFF 中，Y 轴通常是从上到下的，因此我们需要将 Y 值的顺序进行反转
transform = from_origin(np.min(grid_x), np.max(grid_y), 
                        (np.max(grid_x) - np.min(grid_x)) / 100,  # X 轴的分辨率
                        (np.max(grid_y) - np.min(grid_y)) / 100)  # Y 轴的分辨率

# 保存为 GeoTIFF
output_dem = 'output_dem.tif'  # 保存路径

with rasterio.open(output_dem, 'w', driver='GTiff', 
                   height=grid_z_flipped.shape[0], width=grid_z_flipped.shape[1], 
                   count=1, dtype=grid_z_flipped.dtype, crs=CRS.from_epsg(4544),  # 使用EPSG:4544坐标系
                   transform=transform) as dst:
    dst.write(grid_z_flipped, 1)

print(f"DEM 已保存为 {output_dem}")

import os
import rasterio
from rasterio.mask import mask
import shapefile  # <--- 换用这个库，它非常稳定
import numpy as np

# ================= 配置路径 =================
# 1. 你的面 SHP 文件路径
shp_path = 面shp

# 2. 你的 TIF 文件路径
tif_path = DEM 
# 如果上面那个不存在，先用原始DEM测一下：
# tif_path = r"F:\名人堂\许英杰项目\泥石流物源体积计算\九寨沟数据\剖面线2数据测试\c2020年核心区DEM5m_Clip1_Clip21.tif"

# 3. 输出路径
output_path = "final_clip_test.tif"
# ===========================================

def clip_raster_by_shp(raster_path, shp_path, custom_name="clip_interpolated"):
    print(f"--- 开始执行裁剪 ---")
    print(f"输入 DEM: {raster_path}")
    print(f"裁剪边界: {shp_path}")
    
    final_output_path = None

    # 1. 读取 SHP 几何体 (Safe Mode)
    try:
        sf = shapefile.Reader(shp_path)
        geoms = []
        for shape_rec in sf.shapeRecords():
            geoms.append(shape_rec.shape.__geo_interface__)
        print(f"✅ SHP 读取成功，包含 {len(geoms)} 个几何要素")
    except Exception as e:
        print(f"❌ SHP 读取失败: {e}")
        return None

    # 2. 执行裁剪
    try:
        with rasterio.open(raster_path) as src:
            # 尝试 mask 裁剪
            try:
                out_image, out_transform = mask(src, geoms, crop=True, nodata=0)
            except ValueError:
                print("❌ 裁剪失败：SHP 与 DEM 无重叠区域！")
                return None

            # 检查是否为空
            if np.all(out_image == 0):
                print("⚠️ 警告：裁剪结果全为 0")

            # 构建输出文件名
            # 这里简化逻辑，直接用 custom_name 防止字段读取出错
            filename = f"{custom_name}.tif"
            final_output_path = os.path.join(os.path.dirname(raster_path), filename)

            # 更新元数据
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": 0
            })

            # 写入文件
            with rasterio.open(final_output_path, "w", **out_meta) as dest:
                dest.write(out_image)
            
            print(f"✅ 裁剪文件已生成: {final_output_path}")

    except Exception as e:
        print(f"❌ 裁剪过程出错: {e}")
        return None

    # 【核心修复】：必须把路径 return 出去，否则外面接收到的是 None
    return final_output_path

# -------------------------- 执行逻辑 --------------------------

# 1. 执行裁剪，并把结果赋值给 outtif_裁剪
# 注意：这里传入的是 output_dem (插值生成的图) 和 面shp (你的GD02.shp)
outtif_裁剪 = clip_raster_by_shp(output_dem, 面shp)

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from osgeo import gdal, gdalconst

# -------------------------- 配置参数 --------------------------
# 输出的临时对齐文件（原始DEM对齐后的结果）
outputfilePath = 'Aligned_Reference_DEM.tif'
# 新增：为了保证行列数一致，输入文件也需要对齐分辨率，生成一个临时文件
input_aligned_path = 'Aligned_Input_Resampled.tif' 

# 输入文件：即上一步生成的裁剪后的TIF (小范围)
# inputfilePath = outtif_裁剪 # (保持你的变量名)
inputfilePath = outtif_裁剪 # 测试用，请保留你原来的变量

# 参考文件：即原始的大范围 DEM
# referencefilefilePath = DEM # (保持你的变量名)
referencefilefilePath = DEM # 测试用，请保留你原来的变量
# -------------------------------------------------------------

def Reproject_Reference_To_Input():
    """
    【修改后】：
    1. 获取 inputfilePath 的【范围】(Bounds)。
    2. 获取 referencefilefilePath 的【分辨率】(Resolution)。
    3. 将两者都重投影到这个新的统一网格上，确保行列数完全一致。
    """
    print(f"正在执行对齐：范围跟随裁剪图，分辨率跟随原始图...")
    
    # 1. 打开“裁剪图”获取范围 (Bounds)
    in_ds = gdal.Open(inputfilePath, gdal.GA_ReadOnly)
    if in_ds is None: raise ValueError(f"无法打开输入影像: {inputfilePath}")
    in_geo = in_ds.GetGeoTransform()
    in_w = in_ds.RasterXSize
    in_h = in_ds.RasterYSize
    
    # 计算地理边界
    min_x = in_geo[0]
    max_y = in_geo[3]
    max_x = min_x + (in_geo[1] * in_w)
    min_y = max_y + (in_geo[5] * in_h) # 注意 geo[5] 通常是负数

    # 2. 打开“原始大图”获取分辨率 (Resolution)
    ref_ds = gdal.Open(referencefilefilePath, gdal.GA_ReadOnly)
    if ref_ds is None: raise ValueError(f"无法打开参考影像: {referencefilefilePath}")
    ref_geo = ref_ds.GetGeoTransform()
    
    target_res_x = ref_geo[1]        # 原始 X 分辨率
    target_res_y = ref_geo[5]        # 原始 Y 分辨率 (负值)

    # 3. 计算新的图像尺寸 (Cols, Rows)
    # 逻辑：(地理宽度 / 原始像元宽度)
    new_cols = int((max_x - min_x) / target_res_x)
    new_rows = int((min_y - max_y) / target_res_y) 
    
    print(f"新网格设定 -> 分辨率: {target_res_x}, 尺寸: {new_cols}x{new_rows}")

    # 定义新的 GeoTransform (左上角坐标用裁剪图的，分辨率用原始图的)
    target_geo = (min_x, target_res_x, 0, max_y, 0, target_res_y)
    
    # 定义内部重投影函数 (避免重复写代码)
    def reproject_worker(src_ds, out_path):
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(out_path, new_cols, new_rows, 1, src_ds.GetRasterBand(1).DataType)
        out_ds.SetGeoTransform(target_geo)
        out_ds.SetProjection(in_ds.GetProjection()) # 投影跟随输入图
        
        # 保持 NoData
        nodata = src_ds.GetRasterBand(1).GetNoDataValue()
        if nodata is None: nodata = 0
        out_ds.GetRasterBand(1).SetNoDataValue(nodata)
        
        gdal.ReprojectImage(
            src_ds, 
            out_ds, 
            src_ds.GetProjection(), 
            in_ds.GetProjection(), 
            gdalconst.GRA_Bilinear # 双线性插值，平滑
        )
        out_ds.FlushCache()
        return out_ds

    # 4. 执行对齐
    # (A) 处理原始 DEM -> Aligned_Reference_DEM.tif
    print(f"正在重采样原始 DEM...")
    reproject_worker(ref_ds, outputfilePath)
    
    # (B) 【关键步骤】处理裁剪 DEM -> Aligned_Input_Resampled.tif
    # 必须把输入图也转换到这个分辨率，否则矩阵没法相减
    print(f"正在重采样输入 DEM 以匹配分辨率...")
    reproject_worker(in_ds, input_aligned_path)
    
    print(f"✅ 对齐完成。")
    # 这里不需要返回 dataset，因为我们在 compute 中会重新打开文件

def compute_volume_difference():
    """
    计算体积差（修复版：增加强制数值范围过滤，防止 NoData 导致数值爆炸）
    """
    # 1. 读取对齐后的文件
    ds_new = gdal.Open(input_aligned_path)  # Top
    ds_ref = gdal.Open(outputfilePath)      # Bottom
    
    if ds_new is None or ds_ref is None:
        raise ValueError("无法打开对齐后的文件，请检查对齐步骤。")

    band_new = ds_new.GetRasterBand(1)
    band_ref = ds_ref.GetRasterBand(1)
    
    data_new = band_new.ReadAsArray().astype(float)
    data_ref = band_ref.ReadAsArray().astype(float)
    
    # ------------------ 【Debug 核心】 ------------------
    # 打印一下原始数据的极值，看看是不是有 -3.4e+38 这种数
    print(f"Input 数据极值: Min={np.nanmin(data_new):.2e}, Max={np.nanmax(data_new):.2e}")
    print(f"Ref   数据极值: Min={np.nanmin(data_ref):.2e}, Max={np.nanmax(data_ref):.2e}")
    # ----------------------------------------------------

    # 获取分辨率
    gt = ds_new.GetGeoTransform()
    pixel_area = abs(gt[1] * gt[5])
    print(f"单像元面积: {pixel_area:.2f} m²")

    # 2. 【强力掩膜】创建有效区域
    # 即使读取了 NoDataValue，有时候数据里会有微小误差导致 != NoDataValue 失效
    # 所以最稳妥的方法是：只保留地球上合理的高程范围（例如 -500米 到 9000米）
    
    min_valid_elevation = -500   # 根据你的研究区调整，一般不用动
    max_valid_elevation = 9000   # 珠穆朗玛峰也就8848
    
    # 逻辑：非0 且 在合理高程范围内
    mask_new = (data_new != 0) & (data_new > min_valid_elevation) & (data_new < max_valid_elevation)
    mask_ref = (data_ref != 0) & (data_ref > min_valid_elevation) & (data_ref < max_valid_elevation)
    
    # 取交集
    valid_mask = mask_new & mask_ref
    
    count_pixels = np.sum(valid_mask)
    print(f"有效计算像元数: {count_pixels}")
    
    if count_pixels == 0:
        print("⚠️ 警告：有效区域为 0！请检查 min_valid_elevation 设置或坐标系重叠情况。")
        return None, None, data_new

    # 3. 计算高程差
    elevation_diff = np.full_like(data_new, np.nan)
    
    # 只有在 mask 为 True 的地方才进行减法
    elevation_diff[valid_mask] = data_new[valid_mask] - data_ref[valid_mask]
    
    # 4. 计算体积
    # 这里再次过滤一下 diff，防止异常的高差（例如突变 1000米）
    # 假设泥石流或地形变化不会超过 +/- 200米（根据实际情况可调整）
    diff_values = elevation_diff[valid_mask]
    
    # (可选) 剔除极端异常值：例如高差超过 500米的可能是边缘伪影
    # valid_diff_mask = np.abs(diff_values) < 500 
    # final_diff_sum = np.nansum(diff_values[valid_diff_mask])
    
    final_diff_sum = np.nansum(diff_values) # 暂时不剔除，先看结果
    
    total_volume = abs(final_diff_sum) * pixel_area
    
    print(f"------------------------------------------------")
    print(f"📊 修正后体积计算结果: {total_volume:.2f} 立方米")
    print(f"------------------------------------------------")
    
    return valid_mask, elevation_diff, data_new

def plot_3d_cubes_with_surface(valid_mask, elevation_diff, data_new):
    """
    3D 可视化修正版 (V2)：
    1. 灰色底面 = inputfilePath (data_new) 【已按要求修正】
    2. 彩色面   = referencefilePath (通过 data_new - diff 还原)
    """
    if valid_mask is None or np.sum(valid_mask) == 0:
        return

    # --- 1. 降采样 (防止点太多卡死) ---
    points_count = np.sum(valid_mask)
    skip = 1
    if points_count > 10000:
        skip = int(np.sqrt(points_count / 3000)) 
        print(f"绘图降采样倍数: {skip}x")

    # 获取有效数据的行列号
    rows, cols = np.where(valid_mask)
    
    # 应用降采样
    rows = rows[::skip]
    cols = cols[::skip]
    
    # --- 2. 提取高程数据 ---
    
    # 【修正】：z_base (灰色底面) 直接使用 inputfilePath (data_new)
    z_base = data_new[rows, cols]
    
    # diff: 高程差
    diff = elevation_diff[rows, cols]
    
    # z_colored: 另一个面 (Reference)
    # 因为: diff = new - ref  --->  ref = new - diff
    z_colored = z_base - diff

    # --- 3. 开始绘图 ---
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # A. 绘制灰色底面 (User 指定: inputfilePath)
    ax.scatter(cols, rows, z_base, s=1, c='gray', alpha=0.3, label='Base (Input)')

    # B. 绘制彩色面 (Reference)
    # 颜色依然使用 diff，这样可以看出相对于底面是高了还是低了
    p = ax.scatter(cols, rows, z_colored, c=diff, cmap='jet', s=3, alpha=0.9, label='Target (Ref)')
    
    # --- 4. 美化 ---
    cbar = fig.colorbar(p, ax=ax, shrink=0.6, pad=0.1)
    cbar.set_label('Difference (m)')

    ax.set_xlabel('X (Column)')
    ax.set_ylabel('Y (Row)')
    ax.set_zlabel('Elevation (m)')
    ax.set_title(f'3D Visualization\nGray=Input(Base), Color=Reference')
    
    # 调整视角
    ax.view_init(elev=30, azim=-60)
    
    plt.show()

def main_volume_calc():
    try:
        # 1. 对齐影像 (内部生成两个对齐后的临时文件)
        Reproject_Reference_To_Input()
        
        # 2. 计算体积 (读取那两个临时文件)
        valid_mask, elevation_diff, data_new = compute_volume_difference()
        
        # 3. 绘图
        plot_3d_cubes_with_surface(valid_mask, elevation_diff, data_new)
        
    except Exception as e:
        print(f"❌ 计算过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main_volume_calc()