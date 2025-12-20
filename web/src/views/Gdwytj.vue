<template>
  <div class="flex flex-col h-screen w-screen text-white inset-0 m-0 p-0 overflow-hidden bg-cover bg-center">
    <header class="flex items-center px-5">
      <button
        @click="goHome"
        class="mr-4  bg-gray-100 text-slate-900 hover:bg-gray-300 h-full grid place-items-center rounded-l-lg"
        aria-label="返回主页"
      >
      <div class="px-4 text-2xl">返回</div>
        
      </button>
      <div class="flex-1 text-center bg-gray-100 text-black py-6 px-10 rounded-r-lg text-3xl font-bold tracking-wide select-none">
        沟道物源体积
      </div>
    </header>

    <!-- 主内容区：左右分栏 -->
    <div class="flex flex-1 p-4 gap-4">
      <!-- 左侧：控制与文件区 -->
      <aside class="w-80 max-w-[28rem] flex-shrink-0 rounded-lg border border-gray-200 bg-gray-100 p-4 text-slate-900">
        <!-- 子功能标签（水平排列） -->
        
        <div class="flex gap-2 mb-4 pb-4">
          <button
            @click="activeTab = 'surface'"
            :class="activeTab === 'surface' ? 'px-3 py-2 rounded-md bg-blue-600 text-white' : 'px-3 py-2 rounded-md bg-gray-200 text-slate-900 hover:bg-gray-300'"
          >
            底面构建
          </button>
          <button
            @click="activeTab = 'volume'"
            :class="activeTab === 'volume' ? 'px-3 py-2 rounded-md bg-blue-600 text-white' : 'px-3 py-2 rounded-md bg-gray-200 text-slate-900 hover:bg-gray-300'"
          >
            体积计算
          </button>
        </div>
<div class="mb-3 text-lg font-bold text-slate-700 pb-4">输入文件:</div>
        <!-- 地面构建 -->
        <div v-if="activeTab === 'surface'" class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">Shapefile（可多选 .shp/.shx/.dbf/.prj）</label>
            <input
              type="file"
              multiple
              accept=".shp,.shx,.dbf,.prj"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onSurfaceShpChange"
            />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">KML</label>
            <input
              type="file"
              accept=".kml"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onSurfaceKmlChange"
            />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">DEM（输入）</label>
            <input
              type="file"
              accept=".tif,.dem,.asc"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onSurfaceDemChange"
            />
          </div>
        </div>

        <!-- 体积计算 -->
        <div v-else class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">DEM1</label>
            <input
              type="file"
              accept=".tif,.dem,.asc"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onVolumeDem1Change"
            />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">DEM2</label>
            <input
              type="file"
              accept=".tif,.dem,.asc"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onVolumeDem2Change"
            />
          </div>
        </div>

        <div class="mt-6 pt-10">
          <div class="mb-3 text-lg font-bold text-slate-700 py-4">输出文件:</div>
          <div v-if="currentStatus === 'done'" class="mt-4 space-y-2">
            <div v-if="activeTab === 'volume'">
              <div>体积结果：<span class="font-mono">{{ volumeResult.value }}</span></div>
              <a
                v-if="volumeResult.fileUrl"
                :href="volumeResult.fileUrl"
                :download="volumeResult.fileName"
                class="inline-block px-3 py-2 rounded-md bg-green-600 text-white hover:bg-green-700"
              >
                下载结果文件
              </a>
            </div>
            <div v-else>
              <div>已生成 DEM 文件</div>
              <a
                v-if="surfaceResult.fileUrl"
                :href="surfaceResult.fileUrl"
                :download="surfaceResult.fileName"
                class="inline-block px-3 py-2 rounded-md bg-green-600 text-white hover:bg-green-700"
              >
                下载 DEM
              </a>
            </div>
          </div>
        </div>
        <div class="pt-10">
          <button
            class="w-full py-2 rounded-md transition"
            :class="currentStatus === 'running' ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[.99]'"
            :disabled="currentStatus === 'running'"
            @click="onActionClick"
          >
            {{ computeButtonText }}
          </button>
        </div>
      </aside>

      <!-- 右侧：画面展示（主要区域） -->
      <main class="flex-1 rounded-lg border border-gray-200 bg-gray-100 overflow-hidden grid place-items-center">
        <img v-if="currentPreviewUrl" :src="currentPreviewUrl" class="max-w-full max-h-full object-contain" />
      </main>
    </div>
  </div>
  </template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { decode } from 'tiff'

const router = useRouter()
const activeTab = ref('surface')

// 地面构建
const surfaceShpFiles = ref(null)
const surfaceKmlFile = ref(null)
const surfaceDemInput = ref(null)

// 体积计算
const volumeDem1File = ref(null)
const volumeDem2File = ref(null)

const surfaceStatus = ref('idle')
const surfaceResult = ref({ value: null, fileUrl: '', fileName: 'surface_result.tif' })
const surfacePreviewUrl = ref('')

const volumeStatus = ref('idle')
const volumeResult = ref({ value: null, fileUrl: '', fileName: 'volume_result.json' })
const volumePreviewUrl = ref('')

const computeButtonText = computed(() => {
  if (currentStatus.value === 'running') return '正在计算'
  if (currentStatus.value === 'done') return '重新计算'
  return '开始计算'
})

const renderTiffToDataUrl = async (blob) => {
  try {
    const arrayBuffer = await blob.arrayBuffer()
    const ifds = decode(arrayBuffer)
    if (!ifds || ifds.length === 0) return ''
    
    const ifd = ifds[0]
    const { width, height, data } = ifd
    // Estimate channels
    const totalPixels = width * height
    const channels = data.length / totalPixels
    
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    const imageData = ctx.createImageData(width, height)
    const output = imageData.data
    
    if (channels === 1) {
      // Single channel (Grayscale/DEM) - Normalize to 0-255
      let min = Infinity, max = -Infinity
      for (let i = 0; i < data.length; i++) {
        if (data[i] < min) min = data[i]
        if (data[i] > max) max = data[i]
      }
      const range = max - min || 1
      
      for (let i = 0; i < totalPixels; i++) {
        const val = data[i]
        const norm = Math.floor(((val - min) / range) * 255)
        const pos = i * 4
        output[pos] = norm     // R
        output[pos + 1] = norm // G
        output[pos + 2] = norm // B
        output[pos + 3] = 255  // Alpha
      }
    } else if (channels >= 3) {
      // RGB or RGBA
      for (let i = 0; i < totalPixels; i++) {
        const srcPos = i * channels
        const destPos = i * 4
        output[destPos] = data[srcPos]
        output[destPos + 1] = data[srcPos + 1]
        output[destPos + 2] = data[srcPos + 2]
        output[destPos + 3] = channels > 3 ? data[srcPos + 3] : 255
      }
    }
    
    ctx.putImageData(imageData, 0, 0)
    return canvas.toDataURL('image/png')
  } catch (e) {
    console.error('TIFF render error:', e)
    return ''
  }
}

const runComputeSurface = async () => {
  surfaceStatus.value = 'running'
  // Mock delay
  await new Promise(r => setTimeout(r, 1200))
  
  const name = 'surface_result.tif'
  // Use input file if available to demonstrate TIFF rendering, otherwise mock blob
  const blob = surfaceDemInput.value || new Blob(['DEM'], { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  surfaceResult.value = { value: null, fileUrl: url, fileName: name }
  
  const tiffUrl = await renderTiffToDataUrl(blob)
  if (tiffUrl) {
    surfacePreviewUrl.value = tiffUrl
  } else {
    surfacePreviewUrl.value = createPreview('surface', null)
  }
  
  surfaceStatus.value = 'done'
}

const runComputeVolume = () => {
  volumeStatus.value = 'running'
  setTimeout(() => {
    const volume = Math.round(Math.random() * 100000) / 10
    const name = 'volume_result.json'
    const blob = new Blob([JSON.stringify({ volume })], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    volumeResult.value = { value: volume, fileUrl: url, fileName: name }
    volumePreviewUrl.value = createPreview('volume', volume)
    volumeStatus.value = 'done'
  }, 1200)
}

const resetForm = () => {
  if (activeTab.value === 'surface') {
    surfaceShpFiles.value = null
    surfaceKmlFile.value = null
    surfaceDemInput.value = null
    surfaceStatus.value = 'idle'
    surfaceResult.value = { value: null, fileUrl: '', fileName: 'surface_result.tif' }
    surfacePreviewUrl.value = ''
  } else {
    volumeDem1File.value = null
    volumeDem2File.value = null
    volumeStatus.value = 'idle'
    volumeResult.value = { value: null, fileUrl: '', fileName: 'volume_result.json' }
    volumePreviewUrl.value = ''
  }
}

const goHome = () => {
  router.push({ name: 'home' })
}

// 文件选择处理
const onSurfaceShpChange = (e) => {
  surfaceShpFiles.value = e.target.files
}
const onSurfaceKmlChange = (e) => {
  surfaceKmlFile.value = e.target.files?.[0] ?? null
}
const onSurfaceDemChange = (e) => {
  surfaceDemInput.value = e.target.files?.[0] ?? null
}
const onVolumeDem1Change = (e) => {
  volumeDem1File.value = e.target.files?.[0] ?? null
}
const onVolumeDem2Change = (e) => {
  volumeDem2File.value = e.target.files?.[0] ?? null
}

const onActionClick = () => {
  if (activeTab.value === 'surface') {
    if (surfaceStatus.value === 'idle') {
      runComputeSurface()
    } else if (surfaceStatus.value === 'done') {
      surfaceStatus.value = 'idle'
      surfaceResult.value = { value: null, fileUrl: '', fileName: 'surface_result.tif' }
      surfacePreviewUrl.value = ''
      runComputeSurface()
    }
  } else {
    if (volumeStatus.value === 'idle') {
      runComputeVolume()
    } else if (volumeStatus.value === 'done') {
      volumeStatus.value = 'idle'
      volumeResult.value = { value: null, fileUrl: '', fileName: 'volume_result.json' }
      volumePreviewUrl.value = ''
      runComputeVolume()
    }
  }
}

const currentStatus = computed(() =>
  activeTab.value === 'surface' ? surfaceStatus.value : volumeStatus.value
)
const currentPreviewUrl = computed(() =>
  activeTab.value === 'surface' ? surfacePreviewUrl.value : volumePreviewUrl.value
)
const createPreview = (type, value) => {
  const c = document.createElement('canvas')
  c.width = 640
  c.height = 360
  const ctx = c.getContext('2d')
  const grad = ctx.createLinearGradient(0, 0, c.width, c.height)
  if (type === 'surface') {
    grad.addColorStop(0, '#1e3a8a')
    grad.addColorStop(1, '#93c5fd')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, c.width, c.height)
  } else {
    grad.addColorStop(0, '#065f46')
    grad.addColorStop(1, '#34d399')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, c.width, c.height)
    const barW = 60
    const barH = Math.min(300, Math.max(20, (value || 0) / 500))
    ctx.fillStyle = '#064e3b'
    ctx.fillRect(c.width / 2 - barW / 2, c.height - barH - 20, barW, barH)
  }
  return c.toDataURL('image/png')
}
</script>

<style scoped>
</style>
