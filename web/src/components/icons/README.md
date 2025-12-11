# 图标组件库

本项目包含了一系列自定义的图标组件，用于岩体结构面识别与稳定性快速评价系统。

## 图标列表

### 基础操作图标
- `IconNewFile` - 新建文件
- `IconOpenFolder` - 打开文件夹
- `IconSave` - 保存
- `IconPrint` - 打印
- `IconSearch` - 查找

### 视图控制图标
- `IconZoomIn` - 放大
- `IconZoomOut` - 缩小
- `IconFitToScreen` - 视角调整到合适大小
- `IconDrag` - 拖动

### 方向图标
- `IconArrowUp` - 朝上
- `IconArrowRight` - 朝右

### 地理相关图标
- `IconNorthPole` - 北极
- `IconCompass` - 指南针
- `IconHeatmapEarth` - 热力图地球
- `IconLatLonEarth` - 经纬度地球
- `IconGridEarth` - 网格地球

### 测量工具图标
- `IconAngleMeasurement` - 测量两点与地心之间的夹角
- `IconSlopeMeasurement` - 测量坡度

### 几何图形图标
- `IconCone` - 圆锥
- `IconOvalBox` - 椭圆方框
- `IconRegularHexagon` - 普通六边形
- `IconIncompleteHexagon` - 六边形有六个点但左下的边缺失

### 其他图标
- `IconBreak` - 断裂
- `IconDiscrete` - 离散
- `IconExclude` - 不包括
- `IconAddText` - 添加文本
- `IconSitArrow` - 坐上箭头
- `IconSlash` - 斜杠

## 使用方法

### 1. 导入图标组件

```vue
<script setup>
import { IconNewFile, IconSave } from '@/components/icons'
</script>
```

### 2. 在模板中使用

```vue
<template>
  <div>
    <IconNewFile class="w-6 h-6 text-blue-500" />
    <IconSave class="w-6 h-6 text-green-500" />
  </div>
</template>
```

### 3. 批量导入所有图标

```vue
<script setup>
import * as Icons from '@/components/icons'
</script>
```

## 图标属性

所有图标组件都支持以下属性：

- `width` - 宽度
- `height` - 高度
- `class` - CSS类名
- `style` - 内联样式

## 自定义颜色

图标使用 `currentColor` 作为填充色，可以通过CSS的 `color` 属性来自定义颜色：

```vue
<IconNewFile class="text-blue-500" />
<IconSave class="text-green-500" />
<IconPrint class="text-red-500" />
```

## 响应式设计

图标组件使用 `preserveAspectRatio="xMidYMid meet"` 确保在不同尺寸下保持比例。

## 浏览器兼容性

所有图标都使用SVG格式，支持现代浏览器，包括：
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 许可证

这些图标组件遵循与项目相同的许可证。
