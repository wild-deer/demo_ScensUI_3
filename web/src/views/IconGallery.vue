<template>
  <div class="p-5 max-w-6xl mx-auto">
    <h1 class="text-center mb-8 text-slate-800 text-3xl font-bold">图标库</h1>
    <div class="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-5">
      <div 
        class="flex flex-col items-center p-5 border border-gray-200 rounded-lg bg-white transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:border-emerald-500" 
        v-for="icon in icons" 
        :key="icon.name"
      >
        <component :is="icon.component" class="w-12 h-12 mb-2.5 text-emerald-500" />
        <span class="text-center text-sm text-gray-600 leading-relaxed break-words">{{ icon.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  IconNewFile,
  IconOpenFolder,
  IconSave,
  IconPrint,
  IconSearch,
  IconZoomIn,
  IconZoomOut,
  IconFitToScreen,
  IconDrag,
  IconArrowUp,
  IconArrowRight,
  IconNorthPole,
  IconCompass,
  IconBreak,
  IconDiscrete,
  IconHeatmapEarth,
  IconLatLonEarth,
  IconGridEarth,
  IconAngleMeasurement,
  IconSlopeMeasurement,
  IconCone,
  IconExclude,
  IconAddText,
  IconSitArrow,
  IconOvalBox,
  IconSlash,
  IconIncompleteHexagon,
  IconRegularHexagon,
  IconTuoPu,
  IconAnTiTuoPu,
  IconLength,
  IconRactagle
} from '@/components/icons'

const icons = [
  { name: '新建文件', component: IconNewFile },
  { name: '打开文件夹', component: IconOpenFolder },
  { name: '保存', component: IconSave },
  { name: '打印', component: IconPrint },
  { name: '查找', component: IconSearch },
  { name: '放大', component: IconZoomIn },
  { name: '缩小', component: IconZoomOut },
  { name: '视角调整到合适大小', component: IconFitToScreen },
  { name: '拖动', component: IconDrag },
  { name: '朝上', component: IconArrowUp },
  { name: '朝右', component: IconArrowRight },
  { name: '北极', component: IconNorthPole },
  { name: '指南针', component: IconCompass },
  { name: '断裂', component: IconBreak },
  { name: '离散', component: IconDiscrete },
  { name: '测量', component: IconLength },
  { name: '拓扑', component: IconTuoPu },
  { name: '反拓扑', component: IconAnTiTuoPu },
  { name: '热力图地球', component: IconHeatmapEarth },
  { name: '经纬度地球', component: IconLatLonEarth },
  { name: '网格地球', component: IconGridEarth },
  { name: '测量两点与地心之间的夹角', component: IconAngleMeasurement },
  { name: '测量坡度', component: IconSlopeMeasurement },
  { name: '圆锥', component: IconCone },
  { name: '不包括', component: IconExclude },
  { name: '添加文本', component: IconAddText },
  { name: '坐上箭头', component: IconSitArrow },
  { name: '椭圆方框', component: IconOvalBox },
  { name: '矩形', component: IconRactagle },
  { name: '斜杠', component: IconSlash },
  { name: '六边形有六个点但左下的边缺失', component: IconIncompleteHexagon },
  { name: '普通六边形', component: IconRegularHexagon }
]
</script>


