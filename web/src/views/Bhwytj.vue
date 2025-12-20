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
        崩滑物源体积
      </div>
    </header>

    <div class="flex flex-1 p-4 gap-4">
      <aside class="w-80 max-w-[28rem] flex-shrink-0 rounded-lg border border-gray-200 bg-gray-100 p-4 text-slate-900">
        <div class="mb-3 text-lg font-bold text-slate-700 pb-4">输入文件</div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">DEM</label>
            <input
              type="file"
              accept=".tif,.dem,.asc"
              class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
              @change="onDemChange"
            />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">迭代次数</label>
            <input
              v-model.number="iterations"
              type="number"
              min="1"
              placeholder="例如：10"
              class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div class="mt-6 pt-10">
          <div class="mb-3 text-lg font-bold text-slate-700 py-4">输出文件</div>
          <div v-if="status === 'done'" class="mt-4 space-y-2">
            <div>ID：<span class="font-mono">{{ result.id }}</span></div>
            <div>体积差（m³）：<span class="font-mono">{{ result.value }}</span></div>
            <div class="flex flex-col gap-2 pt-2">
              <a
                v-if="result.calculated_tif_url"
                :href="result.calculated_tif_url"
                class="inline-block px-3 py-2 rounded-md bg-green-600 text-white hover:bg-green-700"
              >下载计算后 SLBL tif</a>
              <a
                v-if="result.reprojected_tif_url"
                :href="result.reprojected_tif_url"
                class="inline-block px-3 py-2 rounded-md bg-green-600 text-white hover:bg-green-700"
              >下载重投影结果 tif</a>
              <a
                v-if="result.input_tif_url"
                :href="result.input_tif_url"
                class="inline-block px-3 py-2 rounded-md bg-green-600 text-white hover:bg-green-700"
              >下载原始上传 tif</a>
            </div>
          </div>
        </div>
        <div class="pt-10">
          <button
            class="w-full py-2 rounded-md transition"
            :class="status === 'running' || !demFile ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[.99]'"
            :disabled="status === 'running' || !demFile"
            @click="onActionClick"
          >
            {{ buttonText }}
          </button>
          <div v-if="errorMessage" class="mt-3 text-red-600 text-sm">{{ errorMessage }}</div>
        </div>

        <div class="mt-6 border-t border-gray-300 pt-4">
          <label class="block text-sm font-bold text-slate-700 mb-2">图片高度控制</label>
          <input 
            type="range" 
            min="100" 
            max="1200" 
            v-model="previewHeight" 
            class="range range-primary range-sm w-full" 
          />
          <div class="flex justify-between text-xs text-gray-500 mt-1">
            <span>小</span>
            <span>{{ previewHeight }}px</span>
            <span>大</span>
          </div>
        </div>
      </aside>

      <main class="flex-1 rounded-lg border border-gray-200 bg-gray-100 overflow-hidden grid place-items-center relative">
        <img v-if="previewUrl" :src="previewUrl" :style="{ height: previewHeight + 'px' }" class="object-contain max-w-full transition-all duration-200" />
         <div v-else class="flex-1 flex items-center justify-center text-gray-400">
           <div class="text-center">
             <div class="text-4xl mb-2">📊</div>
             <div>结果预览区域</div>
           </div>
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
const demFile = ref(null)
const iterations = ref(10)
const previewHeight = ref(500)

const status = ref('idle')
const result = ref({ id: '', value: null, calculated_tif_url: '', reprojected_tif_url: '', input_tif_url: '' })
const previewUrl = ref('')
const errorMessage = ref('')
const API_URL = import.meta.env.VITE_API_URL || ''
const BASE_URL = API_URL.endsWith('/') ? API_URL : `${API_URL}/`

const buttonText = computed(() => {
  if (status.value === 'running') return '正在计算'
  if (status.value === 'done') return '重新计算'
  return '开始计算'
})

const normalizeUrl = (u) => {
  if (!u) return ''
  if (/^https?:\/\//i.test(u)) return u
  if (u.startsWith('/')) return BASE_URL + u.slice(1)
  return BASE_URL + u
}

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

const runCompute = async () => {
  if (!demFile.value) {
    errorMessage.value = '请先选择 DEM 文件'
    return
  }
  errorMessage.value = ''
  status.value = 'running'
  try {
    if (!API_URL) {
      throw new Error('未配置后端地址，请设置 VITE_API_URL')
    }
    const fd = new FormData()
    fd.append('file', demFile.value)
    fd.append('max_iter', String(Math.max(1, Number(iterations.value || 1))))
    const endpoint = BASE_URL + 'process-slbl'
    const resp = await fetch(endpoint, { method: 'POST', body: fd })
    if (!resp.ok) throw new Error(`请求失败：${resp.status}`)
    const data = await resp.json()
    result.value = {
      id: data.id ?? '',
      value: data.volume_diff_m3 ?? null,
      calculated_tif_url: normalizeUrl(data.calculated_tif_url),
      reprojected_tif_url: normalizeUrl(data.reprojected_tif_url),
      input_tif_url: normalizeUrl(data.input_tif_url),
    }
    
    // Try to fetch and render the calculated TIFF
    if (result.value.calculated_tif_url) {
      try {
        const tiffResp = await fetch(result.value.calculated_tif_url)
        if (tiffResp.ok) {
          const blob = await tiffResp.blob()
          previewUrl.value = await renderTiffToDataUrl(blob)
        } else {
           previewUrl.value = createPreview(result.value.value || 0)
        }
      } catch (err) {
        console.warn('Failed to fetch/render TIFF:', err)
        previewUrl.value = createPreview(result.value.value || 0)
      }
    } else {
      previewUrl.value = createPreview(result.value.value || 0)
    }
    
    status.value = 'done'
  } catch (e) {
    errorMessage.value = String(e?.message || '未知错误')
    status.value = 'idle'
  }
}

const onActionClick = () => {
  if (status.value === 'idle') {
    runCompute()
  } else if (status.value === 'done') {
    status.value = 'idle'
    result.value = { id: '', value: null, calculated_tif_url: '', reprojected_tif_url: '', input_tif_url: '' }
    previewUrl.value = ''
    runCompute()
  }
}

const onDemChange = (e) => {
  demFile.value = e.target.files?.[0] ?? null
}

const goHome = () => {
  router.push({ name: 'home' })
}

const createPreview = (value) => {
  const c = document.createElement('canvas')
  c.width = 640
  c.height = 360
  const ctx = c.getContext('2d')
  const grad = ctx.createLinearGradient(0, 0, c.width, c.height)
  grad.addColorStop(0, '#7c2d12')
  grad.addColorStop(1, '#fdba74')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, c.width, c.height)
  const barW = 60
  const barH = Math.min(300, Math.max(20, (value || 0) / 500))
  ctx.fillStyle = '#9a3412'
  ctx.fillRect(c.width / 2 - barW / 2, c.height - barH - 20, barW, barH)
  return c.toDataURL('image/png')
}
</script>


