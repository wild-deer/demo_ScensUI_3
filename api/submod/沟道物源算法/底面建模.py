import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import rasterio
from pyproj import Transformer
from fastkml import kml
from pygeoif import geometry
import pandas as pd
import re
import shapefile
import pandas as pd
from scipy import interpolate

# 读取 Shapefile 文件
sf = shapefile.Reader(r"./input/沟道物源算法/边界shp/边界.shp")

# 打开DEM文件并读取坐标信息
with rasterio.open(r"./input/沟道物源算法/c2020年核心区DEM5m_Clip1_Clip21.tif") as dem:
    transform = dem.transform
    elevation = dem.read(1)
    nodata = dem.nodatavals[0]

# 定义坐标系和创建转换器
wgs84 = "EPSG:4326"  # WGS84
cgcs2000 = "EPSG:4544"  # CGCS2000
transformer = Transformer.from_crs(wgs84, cgcs2000, always_xy=True)

# 读取KML文件
kml_file = kml.KML()
with open(r"./input/沟道物源算法/剖面线2.kml", 'rb') as f:
    kml_file.from_string(f.read())

# 提取并转换KML中所有折线段的坐标，分组存储
line_groups = []
features = list(kml_file.features()) # 这里报错Traceback (most recent call last):, line 35, in <module> features = list(kml_file.features()) TypeError: 'list' object is not callable

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

# 读取边界点坐标
# 获取属性表的字段名
fields = sf.fields[1:]  # 排除第一个是删除标识符的字段
field_names = [field[0] for field in fields]

# 查找X, Y, Z列
if 'X' in field_names and 'Y' in field_names and 'Z' in field_names:
    # 提取 X, Y, Z 坐标的属性值
    records = sf.records()
    coordinates = [(record['X'], record['Y'], record['Z']) for record in records]
    
    # 将坐标数据转换为 DataFrame
    coordinates_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z'])
    
    # 保存为 CSV 文件
    coordinates_df.to_csv("DEM边界点坐标.csv", index=False)
    print("坐标已成功保存到CSV文件。")
else:
    print("Shapefile 中没有 X, Y, Z 坐标列，请检查属性表。")

    import pandas as pd

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
