<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
  IconLength,
  IconTuoPu,
  IconAnTiTuoPu,
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
  IconRactagle,
  IconSlash,
  IconIncompleteHexagon,
  IconRegularHexagon
} from '@/components/icons'

const route = useRoute()
const router = useRouter()

const history = ref([])
const transitionName = ref('slide-right')

// 初始化历史记录
onMounted(() => {
  history.value.push(route.fullPath)
})

// 监听路由变化
watch(
  () => route.fullPath,
  (toPath, fromPath) => {
    const toIndex = history.value.indexOf(toPath)
    const fromIndex = history.value.indexOf(fromPath)

    if (toIndex > -1 && toIndex < fromIndex) {
      // 后退操作
      transitionName.value = 'slide-right'
    } else {
      // 前进操作
      transitionName.value = 'slide-left'
      if (fromIndex === history.value.length - 1) {
        history.value.push(toPath)
      }
    }

    // 限制历史记录长度
    if (history.value.length > 10) {
      history.value.shift()
    }
  },
)

// 清除历史记录的方法（可选）
const clearHistory = () => {
  history.value = [route.fullPath]
}

// 控制菜单展开状态
const openSections = ref({
  dataManagement: false,
  structureRecognition: false,
  kinematicAnalysis: true, // 默认展开运动学分析
  sourceEstimation: true   // 默认展开物源估算
})

// 切换菜单段落的展开/收起状态
const toggleSection = (sectionName) => {
  openSections.value[sectionName] = !openSections.value[sectionName]
}

// 导航到具体功能页面
const navigateToPage = (routeName) => {
  router.push({ name: routeName })
}

// 获取当前页面标题
const getCurrentPageTitle = () => {
  const pageMap = {
    'home': '主页',
    'IconGallery': '图标库',
    'StructureRecognition': '结构面智能识别'
  }
  return pageMap[route.name] || '未知页面'
}
</script>

<template>
  <div class="flex h-screen w-screen text-gray-800 bg-gradient-to-br from-white via-gray-50 to-gray-100 select-none">
    <!-- 左侧菜单栏 -->
    <div class="w-80 bg-white/95 backdrop-blur-sm border-r border-gray-200 shadow-lg flex flex-col">
      <!-- 顶部标题 -->
      <div class="p-6 border-b border-gray-200">
        <h1 class="text-3xl font-bold text-center text-blue-600">
          岩体结构面识别与稳定性快速评价系统
        </h1>
      </div>
      
      <!-- 菜单内容 -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- 数据管理 -->
        <div class="mb-4">
          <div 
            @click="toggleSection('dataManagement')"
            class="flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-100 transition-all"
          >
            <div class="w-0 h-0 border-l-6 border-l-gray-600 border-t-3 border-t-transparent border-b-3 border-b-transparent mr-3 transition-transform"
                 :class="{ 'rotate-90': openSections.dataManagement }"></div>
            <span class="font-medium text-2xl">数据管理</span>
          </div>
          <div v-show="openSections.dataManagement" class="ml-6 mt-2 space-y-1">
            <div class="flex items-center p-2 rounded cursor-pointer hover:bg-gray-50 transition-all">
              <div class="w-0 h-0 border-l-4 border-l-gray-400 border-t-2 border-t-transparent border-b-2 border-b-transparent mr-2"></div>
              <span class="text-xl">数据载入</span>
            </div>
            <div class="flex items-center p-2 rounded cursor-pointer hover:bg-gray-50 transition-all">
              <div class="w-0 h-0 border-l-4 border-l-gray-400 border-t-2 border-t-transparent border-b-2 border-b-transparent mr-2"></div>
              <span class="text-xl">绘图选项</span>
            </div>
            <div class="flex items-center p-2 rounded cursor-pointer hover:bg-gray-50 transition-all">
              <div class="w-0 h-0 border-l-4 border-l-gray-400 border-t-2 border-t-transparent border-b-2 border-b-transparent mr-2"></div>
              <span class="text-xl">成果输出</span>
            </div>
          </div>
        </div>

        <!-- 结构面智能识别 -->
        <div class="mb-4">
          <div 
            @click="toggleSection('structureRecognition')"
            class="flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-100 transition-all"
          >
            <div class="w-0 h-0 border-l-6 border-l-gray-600 border-t-3 border-t-transparent border-b-3 border-b-transparent mr-3 transition-transform"
                 :class="{ 'rotate-90': openSections.structureRecognition }"></div>
            <span class="font-medium text-2xl">结构面智能识别</span>
          </div>
          <div v-show="openSections.structureRecognition" class="ml-6 mt-2 space-y-1">
            <div class="flex items-center p-2 rounded cursor-pointer hover:bg-gray-50 transition-all">
              <div class="w-0 h-0 border-l-4 border-l-gray-400 border-t-2 border-t-transparent border-b-2 border-b-transparent mr-2"></div>
              <span class="text-xl">法向量估计</span>
            </div>
            <div class="flex items-center p-2 rounded cursor-pointer hover:bg-gray-50 transition-all">
              <div class="w-0 h-0 border-l-4 border-l-gray-400 border-t-2 border-t-transparent border-b-2 border-b-transparent mr-2"></div>
              <span class="text-xl">核密度估计</span>
            </div>
            <div 
              @click="navigateToPage('StructureRecognition')"
              class="flex items-center p-2 rounded cursor-pointer hover:bg-gray-50 transition-all"
            >
              <div class="w-0 h-0 border-l-4 border-l-gray-400 border-t-2 border-t-transparent border-b-2 border-b-transparent mr-2"></div>
              <span class="text-xl">智能识别</span>
            </div>
          </div>
        </div>

        <!-- 运动学分析 -->
        <div class="mb-4">
          <div 
            @click="toggleSection('kinematicAnalysis')"
            class="flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-100 transition-all"
          >
            <div class="w-0 h-0 border-l-6 border-l-gray-600 border-t-3 border-t-transparent border-b-3 border-b-transparent mr-3 transition-transform"
                 :class="{ 'rotate-90': openSections.kinematicAnalysis }"></div>
            <span class="font-medium text-2xl">运动学分析</span>
          </div>
          <div v-show="openSections.kinematicAnalysis" class="ml-6 mt-2">
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div class="space-y-3 text-base">
                <!-- 破坏类型选择 -->
                <div class="space-y-2">
                  <label class="block text-gray-700 font-medium text-xl">破坏类型:</label>
                  <select class="w-full p-2 border border-gray-300 rounded-md text-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="plane">平面破坏</option>
                    <option value="wedge">楔形体破坏</option>
                    <option value="flexural">弯曲倾倒破坏</option>
                    <option value="direct" selected>直接倾倒破坏</option>
                  </select>
                </div>
                
                <!-- 边坡参数 -->
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <label class="block text-gray-700 font-medium text-xl">边坡倾角:</label>
                    <input type="number" value="42" class="w-full p-2 border border-gray-300 rounded-md text-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                  </div>
                  <div class="space-y-2">
                    <label class="block text-gray-700 font-medium text-xl">边坡倾向:</label>
                    <input type="number" value="150" class="w-full p-2 border border-gray-300 rounded-md text-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                  </div>
                  <div class="space-y-2">
                    <label class="block text-gray-700 font-medium text-xl">摩擦角:</label>
                    <input type="number" value="30" class="w-full p-2 border border-gray-300 rounded-md text-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                  </div>
                  <div class="space-y-2">
                    <label class="block text-gray-700 font-medium text-xl">横向限制:</label>
                    <input type="number" value="20" class="w-full p-2 border border-gray-300 rounded-md text-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                  </div>
                </div>
                
                <!-- 显示选项 -->
                <div class="space-y-2">
                  <div class="flex items-center space-x-2">
                    <input type="checkbox" checked class="w-4 h-4 text-blue-600 focus:ring-blue-500">
                    <span class="text-gray-700 text-xl">构造线显示</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <input type="checkbox" checked class="w-4 h-4 text-blue-600 focus:ring-blue-500">
                    <span class="text-gray-700 text-xl">高亮显示</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 物源估算功能 -->
        
        <!-- 图标库 -->
        <!-- <div class="mb-4">
          <div 
            @click="navigateToPage('IconGallery')"
            class="flex items-center p-3 rounded-lg cursor-pointer hover:bg-gray-100 transition-all"
          >
            <div class="w-0 h-0 border-l-6 border-l-gray-600 border-t-3 border-t-transparent border-b-3 border-b-transparent mr-3"></div>
            <span class="font-medium text-xl">图标库</span>
          </div>
        </div> -->

      </div>
    </div>

    <!-- 右侧主内容区 -->
    <div class="flex-1 flex flex-col">
      <!-- 顶部工具栏 -->
      <div class="h-16 bg-white border-b border-gray-200 shadow-sm flex items-center px-4">
        <div class="flex items-center space-x-4 text-xl">
          <span class="text-gray-600 cursor-pointer hover:text-blue-600">文件</span>
          <span class="text-gray-600 cursor-pointer hover:text-blue-600">编辑</span>
          <span class="text-gray-600 cursor-pointer hover:text-blue-600">分析</span>
          <span class="text-gray-600 cursor-pointer hover:text-blue-600">视图</span>
          <span class="text-gray-600 cursor-pointer hover:text-blue-600">工具</span>
          <span class="text-gray-600 cursor-pointer hover:text-blue-600">帮助</span>
        </div>
        
        <!-- 当前页面显示 -->
        <div class="ml-auto flex items-center space-x-4">
          <span class="text-xl text-gray-500">当前页面: {{ getCurrentPageTitle() }}</span>
 
        </div>
      </div>
      
      <!-- 工具图标栏 -->
      <div class="h-12 bg-gray-50 border-b border-gray-200 flex items-center px-4 space-x-1 overflow-x-auto">
        <!-- 32个图标按钮 -->
        <button class="p-2 hover:bg-gray-200 rounded" title="新建文件">
          <IconNewFile class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="打开文件夹">
          <IconOpenFolder class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="保存">
          <IconSave class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="打印">
          <IconPrint class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="查找">
          <IconSearch class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="放大">
          <IconZoomIn class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="缩小">
          <IconZoomOut class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="视角调整到合适大小">
          <IconFitToScreen class="w-4 h-4 text-gray-600" />
        </button>
        
        <div class="w-px h-6 bg-gray-300"></div>
        
        <button class="p-2 hover:bg-gray-200 rounded" title="拖动">
          <IconDrag class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="朝上">
          <IconArrowUp class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="朝右">
          <IconArrowRight class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="北极">
          <IconNorthPole class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="指南针">
          <IconCompass class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="断裂">
          <IconBreak class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="离散">
          <IconDiscrete class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="测量">
          <IconLength class="w-4 h-4 text-gray-600" />
        </button>
        
        <div class="w-px h-6 bg-gray-300"></div>
        
        <button class="p-2 hover:bg-gray-200 rounded" title="拓扑">
          <IconTuoPu class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="反拓扑">
          <IconAnTiTuoPu class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="热力图地球">
          <IconHeatmapEarth class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="经纬度地球">
          <IconLatLonEarth class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="网格地球">
          <IconGridEarth class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="测量两点与地心之间的夹角">
          <IconAngleMeasurement class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="测量坡度">
          <IconSlopeMeasurement class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="圆锥">
          <IconCone class="w-4 h-4 text-gray-600" />
        </button>
        
        <div class="w-px h-6 bg-gray-300"></div>
        
        <button class="p-2 hover:bg-gray-200 rounded" title="不包括">
          <IconExclude class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="添加文本">
          <IconAddText class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="坐上箭头">
          <IconSitArrow class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="椭圆方框">
          <IconOvalBox class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="矩形">
          <IconRactagle class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="斜杠">
          <IconSlash class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="六边形有六个点但左下的边缺失">
          <IconIncompleteHexagon class="w-4 h-4 text-gray-600" />
        </button>
        <button class="p-2 hover:bg-gray-200 rounded" title="普通六边形">
          <IconRegularHexagon class="w-4 h-4 text-gray-600" />
        </button>
      </div>
      
      <!-- 主工作区 - 带路由过渡动画 -->
      <div class="flex-1 bg-gray-50/80 relative overflow-y-auto">
        <Transition :name="transitionName">
          <RouterView class="absolute inset-0 w-full h-full" :key="route.fullPath" />
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 路由左滑动画（前进） */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.slide-left-enter-from {
  transform: translateX(100%);
}

.slide-left-leave-to {
  transform: translateX(-100%);
}

/* 路由右滑动画（后退） */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.slide-right-enter-from {
  transform: translateX(-100%);
}

.slide-right-leave-to {
  transform: translateX(100%);
}

/* 确保动画容器正确定位 */
.slide-left-enter-active > *,
.slide-left-leave-active > *,
.slide-right-enter-active > *,
.slide-right-leave-active > * {
  height: 100%;
  width: 100%;
}
</style>
