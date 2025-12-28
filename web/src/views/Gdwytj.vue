<template>
  <div class="flex flex-col h-screen w-screen text-white inset-0 m-0 p-0 overflow-hidden bg-cover bg-center">
    <header class="flex items-center px-5">
      <button
        @click="goHome"
        class="mr-4 bg-gray-100 text-slate-900 hover:bg-gray-300 h-full grid place-items-center rounded-l-lg"
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
      <aside class="w-80 max-w-[28rem] flex-shrink-0 rounded-lg border border-gray-200 bg-gray-100 p-4 text-slate-900 overflow-y-auto">
        
        <div class="mb-3 text-lg font-bold text-slate-700 pb-4">输入文件:</div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">原始 DEM 压缩包 (.zip)</label>
            <div class="text-xs text-slate-500 mb-1">压缩包内必须包含 .tif 格式的 DEM 文件</div>
            <input
              type="file"
              accept=".zip"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onDemZipChange"
            />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">边界范围 KML (.kml)</label>
            <input
              type="file"
              accept=".kml"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onBoundaryKmlChange"
            />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">剖面线 KML (.kml)</label>
            <input
              type="file"
              accept=".kml"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onProfileKmlChange"
            />
          </div>
        </div>

        <div v-if="errorMessage" class="mt-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
          {{ errorMessage }}
        </div>

        <div class="mt-6 pt-4">
          <button
            class="w-full py-2 rounded-md transition font-bold"
            :class="status === 'running' ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[.99]'"
            :disabled="status === 'running'"
            @click="onActionClick"
          >
            {{ computeButtonText }}
          </button>
        </div>

        <div class="mt-6 border-t pt-4" v-if="result">
          <div class="mb-3 text-lg font-bold text-slate-700">计算结果:</div>
          
          <div class="mb-4 p-3 bg-white rounded shadow-sm">
            <div class="text-sm text-gray-500">体积 (Volume)</div>
            <div class="text-xl font-mono font-bold text-blue-600">{{ result.volume }} m³</div>
          </div>

          <div class="space-y-2 text-sm">
            <div class="font-semibold text-slate-700">文件下载:</div>
            
            <a v-if="result.files?.generated_dem" :href="result.files.generated_dem" download class="block p-2 bg-white border rounded hover:bg-gray-50 text-blue-600 truncate">
              <i class="fas fa-download mr-2"></i>生成 DEM (.tif)
            </a>
            <a v-if="result.files?.final_clipped_dem" :href="result.files.final_clipped_dem" download class="block p-2 bg-white border rounded hover:bg-gray-50 text-blue-600 truncate">
              <i class="fas fa-download mr-2"></i>裁剪后 DEM (.tif)
            </a>
            <a v-if="result.files?.merged_csv" :href="result.files.merged_csv" download class="block p-2 bg-white border rounded hover:bg-gray-50 text-blue-600 truncate">
              <i class="fas fa-download mr-2"></i>拟合点坐标 (.csv)
            </a>
            <a v-if="result.files?.boundary_csv" :href="result.files.boundary_csv" download class="block p-2 bg-white border rounded hover:bg-gray-50 text-blue-600 truncate">
              <i class="fas fa-download mr-2"></i>边界点坐标 (.csv)
            </a>
             <a v-if="result.files?.bspline_csv" :href="result.files.bspline_csv" download class="block p-2 bg-white border rounded hover:bg-gray-50 text-blue-600 truncate">
              <i class="fas fa-download mr-2"></i>B样条点坐标 (.csv)
            </a>
             <a v-if="result.files?.x123_csv" :href="result.files.x123_csv" download class="block p-2 bg-white border rounded hover:bg-gray-50 text-blue-600 truncate">
              <i class="fas fa-download mr-2"></i>每组 X1_X2_X3 (.csv)
            </a>
          </div>
        </div>
      </aside>

      <!-- 右侧：画面展示（主要区域） -->
      <main class="flex-1 rounded-lg border border-gray-200 bg-gray-100 overflow-hidden grid place-items-center relative">
        <img v-if="previewUrl" :src="previewUrl" :style="{ height: previewHeight + 'px' }" class="object-contain max-w-full transition-all duration-200" />
        <div v-else class="flex-1 flex items-center justify-center text-gray-400">
           <div class="text-center">
             <div class="text-4xl mb-2">📊</div>
             <div>结果预览区域</div>
           </div>
        </div>
        
        <!-- 如果有多个可视化结果，可以添加切换按钮 -->
        <div v-if="result && result.visualization_urls && result.visualization_urls.length > 1" class="absolute bottom-4 left-0 right-0 flex justify-center gap-2">
            <button 
                v-for="(url, index) in result.visualization_urls" 
                :key="index"
                @click="previewUrl = normalizeUrl(url)"
                class="w-3 h-3 rounded-full"
                :class="previewUrl === normalizeUrl(url) ? 'bg-blue-600' : 'bg-gray-400 hover:bg-gray-500'"
            ></button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { decode } from 'tiff'

const router = useRouter()
const API_URL = import.meta.env.VITE_API_URL || ''
const BASE_URL = API_URL.endsWith('/') ? API_URL : `${API_URL}/`

// State
const demZipFile = ref(null)
const boundaryKmlFile = ref(null)
const profileKmlFile = ref(null)
const status = ref('idle') // idle, running, done
const errorMessage = ref('')
const result = ref(null)
const previewUrl = ref('')
const previewHeight = ref(500)

// Helpers
const normalizeUrl = (u) => {
  if (!u) return ''
  if (/^https?:\/\//i.test(u)) return u
  if (u.startsWith('/')) return BASE_URL + u.slice(1)
  return BASE_URL + u
}

const computeButtonText = computed(() => {
  if (status.value === 'running') return '正在计算...'
  if (status.value === 'done') return '重新计算'
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

// File Handlers
const onDemZipChange = (e) => {
  demZipFile.value = e.target.files?.[0] ?? null
}
const onBoundaryKmlChange = (e) => {
  boundaryKmlFile.value = e.target.files?.[0] ?? null
}
const onProfileKmlChange = (e) => {
  profileKmlFile.value = e.target.files?.[0] ?? null
}

const goHome = () => {
  router.push({ name: 'home' })
}

const onActionClick = async () => {
  if (status.value === 'running') return

  // Validation
  if (!demZipFile.value) {
    errorMessage.value = '请上传原始 DEM 压缩包 (.zip)'
    return
  }
  if (!boundaryKmlFile.value) {
    errorMessage.value = '请上传边界范围 KML (.kml)'
    return
  }
  if (!profileKmlFile.value) {
    errorMessage.value = '请上传剖面线 KML (.kml)'
    return
  }

  errorMessage.value = ''
  status.value = 'running'
  result.value = null
  previewUrl.value = ''

  try {
    const formData = new FormData()
    formData.append('dem_zip', demZipFile.value)
    formData.append('boundary_kml', boundaryKmlFile.value)
    formData.append('profile_kml', profileKmlFile.value)

    const response = await fetch(`${BASE_URL}channel-source`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
        let errText = response.statusText;
        try {
            const errJson = await response.json();
            if(errJson.detail) errText = errJson.detail;
        } catch(e) {}
        throw new Error(`请求失败 (${response.status}): ${errText}`)
    }

    const data = await response.json()
    
    // Normalize URLs in the result
    const processedFiles = {}
    if (data.files) {
        for (const [key, url] of Object.entries(data.files)) {
            processedFiles[key] = normalizeUrl(url)
        }
    }
    
    const processedVisUrls = (data.visualization_urls || []).map(normalizeUrl)

    result.value = {
        ...data,
        files: processedFiles,
        visualization_urls: processedVisUrls
    }

    // Determine what to preview: Prioritize DEM TIFF over static visualization
    let demUrl = processedFiles.generated_dem;
    // Fallback to clipped dem if generated_dem is not available
    if (!demUrl && processedFiles.final_clipped_dem) {
        demUrl = processedFiles.final_clipped_dem;
    }

    if (demUrl) {
         // Try to fetch and render the DEM TIFF
        try {
            const tiffResp = await fetch(demUrl)
            if (tiffResp.ok) {
                const blob = await tiffResp.blob()
                const dataUrl = await renderTiffToDataUrl(blob)
                if (dataUrl) {
                    previewUrl.value = dataUrl
                } else {
                     // If TIFF render fails, fallback to vis urls if any
                    if (processedVisUrls.length > 0) previewUrl.value = processedVisUrls[0]
                }
            } else {
                 // If fetch fails, fallback
                 if (processedVisUrls.length > 0) previewUrl.value = processedVisUrls[0]
            }
        } catch (e) {
            console.warn('Failed to render DEM preview:', e)
            if (processedVisUrls.length > 0) previewUrl.value = processedVisUrls[0]
        }
    } else if (processedVisUrls.length > 0) {
        previewUrl.value = processedVisUrls[0]
    }

    status.value = 'done'
  } catch (error) {
    console.error('Computation failed:', error)
    errorMessage.value = '计算出错: ' + error.message
    status.value = 'idle'
  }
}
</script>

<style scoped>
/* 引入 Font Awesome (如果全局没有引入，可以在这里加，或者假设已全局引入) */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css');
</style>
