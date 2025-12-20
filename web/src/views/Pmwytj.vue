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
        坡面物源体积
      </div>
    </header>

    <div class="flex flex-1 p-4 gap-4 overflow-hidden">
      <aside class="w-100 max-w-[28rem] flex-shrink-0 rounded-lg border border-gray-200 bg-gray-100 p-4 text-slate-900 flex flex-col overflow-y-auto">
        <div class="mb-3 text-sm font-semibold text-slate-700">子功能</div>
        <div class="flex gap-2 mb-4 text-[12px] flex-wrap flex-shrink-0">
          <button @click="activeTab = 'c'" :class="tabClass('c')" class="flex-1 min-w-[4rem]">C 因子</button>
          <button @click="activeTab = 'k'" :class="tabClass('k')" class="flex-1 min-w-[4rem]">K 因子</button>
          <button @click="activeTab = 'ls'" :class="tabClass('ls')" class="flex-1 min-w-[4rem]">LS 因子</button>
          <button @click="activeTab = 'p'" :class="tabClass('p')" class="flex-1 min-w-[4rem]">P 因子</button>
          <button @click="activeTab = 'r'" :class="tabClass('r')" class="flex-1 min-w-[4rem]">R 因子</button>
        </div>

        <div class="flex-1 overflow-y-auto pr-1">
          <div class="mb-3 text-lg font-bold text-slate-700 pb-2">输入文件与参数</div>
          
          <!-- C Factor Inputs -->
          <div v-if="activeTab === 'c'" class="space-y-4">
            <div>
              <label class="block text-sm mb-2 text-slate-700">NDVI 文件 (.tif)</label>
              <input type="file" accept=".tif,.tiff" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onCNdviChange" />
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">范围文件 (.zip)</label>
              <div class="text-xs text-gray-500 mb-1">包含 .shp, .shx, .dbf, .prj 的压缩包</div>
              <input type="file" accept=".zip" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onCShpChange" />
            </div>
          </div>

          <!-- K Factor Inputs -->
          <div v-else-if="activeTab === 'k'" class="space-y-4">
            <div>
              <label class="block text-sm mb-2 text-slate-700">栅格文件 (.bil, .zip, .tif)</label>
              <input type="file" accept=".bil,.zip,.tif,.tiff" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onKRasterChange" />
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">属性表 (.xls, .xlsx)</label>
              <input type="file" accept=".xls,.xlsx" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onKAttributeChange" />
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">范围文件 (.zip)</label>
              <input type="file" accept=".zip" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onKShpChange" />
            </div>
          </div>

          <!-- LS Factor Inputs -->
          <div v-else-if="activeTab === 'ls'" class="space-y-4">
            <div>
              <label class="block text-sm mb-2 text-slate-700">DEM 文件 (.tif, .zip)</label>
              <input type="file" accept=".tif,.tiff,.zip" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onLSDemChange" />
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">目标分辨率 (米, 可选)</label>
              <input v-model.number="lsTargetResolution" type="number" min="0.1" step="0.1" placeholder="默认不重采样" class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">重采样方法</label>
              <select v-model="lsResampleMethod" class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="average ">Average</option>
                <option value="bilinear">Bilinear</option>
                <option value="cubic">Cubic</option>
              </select>
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">分块大小 (默认 500)</label>
              <input v-model.number="lsChunkSize" type="number" min="100" step="100" class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <!-- P Factor Inputs -->
          <div v-else-if="activeTab === 'p'" class="space-y-4">
            <div v-if="pStatus === 'idle' || pStatus === 'preparing' || pStatus === 'prepared'">
              <label class="block text-sm mb-2 text-slate-700">分类栅格 (.zip)</label>
              <div class="text-xs text-gray-500 mb-1">包含分类 .tif 的压缩包</div>
              <input type="file" accept=".zip" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onPCategoryChange" />
            </div>
            
            <div v-if="pStatus === 'prepared' || pStatus === 'applying' || pStatus === 'done'" class="bg-white p-3 rounded border border-gray-200">
              <div class="text-sm font-bold mb-2">P 值映射设置</div>
              <div v-if="pValues.length === 0" class="text-sm text-gray-500">未找到分类值</div>
              <div v-else class="max-h-48 overflow-y-auto space-y-2">
                <div v-for="val in pValues" :key="val" class="flex items-center gap-2">
                  <span class="text-sm w-16">类别 {{ val }}:</span>
                  <input 
                    type="number" 
                    v-model.number="pMapping[val]" 
                    step="0.01" 
                    min="0" 
                    max="1" 
                    class="flex-1 px-2 py-1 text-sm border rounded focus:ring-1 focus:ring-blue-500 outline-none"
                    placeholder="P值 (0-1)"
                  >
                </div>
              </div>
            </div>
          </div>

          <!-- R Factor Inputs -->
          <div v-else class="space-y-4">
            <div>
              <label class="block text-sm mb-2 text-slate-700">降雨量年份数据 (.zip)</label>
              <div class="text-xs text-gray-500 mb-1">可多选，每个 Zip 含12个月份数据</div>
              <input type="file" multiple accept=".zip" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onRYearsChange" />
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">范围文件 (.zip)</label>
              <input type="file" accept=".zip" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onRShpChange" />
            </div>
            <div>
              <label class="block text-sm mb-2 text-slate-700">缩放参数 (默认 0.1)</label>
              <input v-model.number="rScaleFactor" type="number" min="0" step="0.01" class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          
          <div v-if="errorMessage" class="mt-4 p-2 bg-red-100 border border-red-300 text-red-700 text-sm rounded">
            {{ errorMessage }}
          </div>
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
        <div class="mt-4 pt-4 border-t border-gray-300 flex-shrink-0">
          <div class="mb-3 text-lg font-bold text-slate-700 py-2">操作与结果</div>
          
          <!-- Result Links -->
          <div v-if="currentStatus === 'done' && currentResult" class="mb-4 space-y-2 text-sm">
            <div class="font-semibold text-green-600">计算完成</div>
            
            <div v-if="currentResult.mainUrl" class="flex items-center justify-between bg-white p-2 rounded border">
              <span>主要结果</span>
              <a :href="currentResult.mainUrl" :download="currentResult.mainName" class="text-blue-600 hover:underline">下载 TIF</a>
            </div>
             <div v-if="currentResult.visUrl" class="flex items-center justify-between bg-white p-2 rounded border">
              <span>可视化图</span>
              <a :href="currentResult.visUrl" download="visualization.png" class="text-blue-600 hover:underline">下载 PNG</a>
            </div>
            <div v-if="currentResult.reportUrl" class="flex items-center justify-between bg-white p-2 rounded border">
              <span>统计报告</span>
              <a :href="currentResult.reportUrl" download="report.txt" class="text-blue-600 hover:underline">下载报告</a>
            </div>
             <div v-if="currentResult.csvUrl" class="flex items-center justify-between bg-white p-2 rounded border">
              <span>CSV 表格</span>
              <a :href="currentResult.csvUrl" download="data.csv" class="text-blue-600 hover:underline">下载 CSV</a>
            </div>

            <!-- R Factor Specific Links -->
            <div v-if="currentResult.yearsUrls && currentResult.yearsUrls.length" class="space-y-1 mt-2">
              <div class="text-xs font-semibold text-gray-600">年份数据下载:</div>
              <div v-for="(url, idx) in currentResult.yearsUrls" :key="idx" class="flex items-center justify-between bg-white p-2 rounded border">
                <span>年份数据 {{ idx + 1 }}</span>
                <a :href="url" :download="`years_data_${idx+1}.zip`" class="text-blue-600 hover:underline">下载</a>
              </div>
            </div>
            <div v-if="currentResult.shpUrl" class="flex items-center justify-between bg-white p-2 rounded border mt-2">
              <span>范围文件</span>
              <a :href="currentResult.shpUrl" download="shp_data.zip" class="text-blue-600 hover:underline">下载 Zip</a>
            </div>
            
            <!-- Stats -->
            <div v-if="currentResult.stats" class="mt-2 text-xs text-gray-600 bg-gray-50 p-2 rounded">
              <div>最小值: {{ currentResult.stats.min?.toFixed(4) }}</div>
              <div>最大值: {{ currentResult.stats.max?.toFixed(4) }}</div>
              <div>平均值: {{ currentResult.stats.mean?.toFixed(4) }}</div>
            </div>
          </div>

          <button
            class="w-full py-2 rounded-md transition font-semibold"
            :class="(currentStatus === 'running' || currentStatus === 'preparing' || currentStatus === 'applying') ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[.99]'"
            :disabled="currentStatus === 'running' || currentStatus === 'preparing' || currentStatus === 'applying'"
            @click="onActionClick"
          >
            {{ buttonText }}
          </button>
        </div>
      </aside>

      <main class="flex-1 rounded-lg border border-gray-200 bg-gray-100 overflow-hidden relative flex flex-col">
        <div v-if="currentPreviewUrl" class="flex-1 overflow-auto flex items-center justify-center p-4">
           <img :src="currentPreviewUrl" :style="{ height: previewHeight + 'px' }" class="object-contain max-w-full transition-all duration-200" />
        </div>
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
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { decode } from 'tiff'

const router = useRouter()
const activeTab = ref('c')
const errorMessage = ref('')
const previewHeight = ref(500)

const API_URL = import.meta.env.VITE_API_URL || ''
const BASE_URL = API_URL.endsWith('/') ? API_URL : `${API_URL}/`

// Helper to normalize URLs
const normalizeUrl = (u) => {
  if (!u) return ''
  if (/^https?:\/\//i.test(u)) return u
  if (u.startsWith('/')) return BASE_URL + u.slice(1)
  return BASE_URL + u
}

// --- C Factor State ---
const cNdviFile = ref(null)
const cShpZip = ref(null)
const cStatus = ref('idle')
const cResult = ref(null)
const cPreviewUrl = ref('')

// --- K Factor State ---
const kRasterFile = ref(null)
const kAttributeFile = ref(null)
const kShpZip = ref(null)
const kStatus = ref('idle')
const kResult = ref(null)
const kPreviewUrl = ref('')

// --- LS Factor State ---
const lsDemFile = ref(null)
const lsTargetResolution = ref(null)
const lsResampleMethod = ref('average')
const lsChunkSize = ref(500)
const lsStatus = ref('idle')
const lsResult = ref(null)
const lsPreviewUrl = ref('')

// --- P Factor State ---
const pCategoryFile = ref(null)
const pValues = ref([])
const pMapping = ref({})
const pStatus = ref('idle') // idle -> preparing -> prepared -> applying -> done
const pResult = ref(null)
const pPreviewUrl = ref('')

// --- R Factor State ---
const rYearsFiles = ref(null)
const rShpZip = ref(null)
const rScaleFactor = ref(0.1)
const rStatus = ref('idle')
const rResult = ref(null)
const rPreviewUrl = ref('')

// --- Shared Logic ---

const tabClass = (key) =>
  activeTab.value === key
    ? 'px-3 py-2 rounded-md bg-blue-600 text-white font-medium shadow-sm'
    : 'px-3 py-2 rounded-md bg-gray-200 text-slate-900 hover:bg-gray-300 transition-colors'

const currentStatus = computed(() => {
  switch (activeTab.value) {
    case 'c': return cStatus.value
    case 'k': return kStatus.value
    case 'ls': return lsStatus.value
    case 'p': return pStatus.value
    default: return rStatus.value
  }
})

const currentResult = computed(() => {
  switch (activeTab.value) {
    case 'c': return cResult.value
    case 'k': return kResult.value
    case 'ls': return lsResult.value
    case 'p': return pResult.value
    default: return rResult.value
  }
})

const currentPreviewUrl = computed(() => {
  switch (activeTab.value) {
    case 'c': return cPreviewUrl.value
    case 'k': return kPreviewUrl.value
    case 'ls': return lsPreviewUrl.value
    case 'p': return pPreviewUrl.value
    default: return rPreviewUrl.value
  }
})

const buttonText = computed(() => {
  const status = currentStatus.value
  if (status === 'running' || status === 'preparing' || status === 'applying') return '处理中...'
  
  if (activeTab.value === 'p') {
    if (status === 'idle') return '上传并解析'
    if (status === 'prepared') return '计算 P 因子'
    if (status === 'done') return '重新开始'
  } else {
    if (status === 'done') return '重新计算'
  }
  
  return '开始计算'
})

// Clear error on tab change
watch(activeTab, () => {
  errorMessage.value = ''
})

const onActionClick = () => {
  errorMessage.value = ''
  if (activeTab.value === 'c') {
    if (cStatus.value === 'idle' || cStatus.value === 'done') runComputeC()
  } else if (activeTab.value === 'k') {
    if (kStatus.value === 'idle' || kStatus.value === 'done') runComputeK()
  } else if (activeTab.value === 'ls') {
    if (lsStatus.value === 'idle' || lsStatus.value === 'done') runComputeLS()
  } else if (activeTab.value === 'p') {
    if (pStatus.value === 'idle') runPrepareP()
    else if (pStatus.value === 'prepared') runApplyP()
    else if (pStatus.value === 'done') {
      // Reset
      pStatus.value = 'idle'
      pResult.value = null
      pPreviewUrl.value = ''
      pValues.value = []
      pMapping.value = {}
      // User needs to upload again or just stay idle? 
      // Let's assume they might want to change file or restart.
    }
  } else {
    if (rStatus.value === 'idle' || rStatus.value === 'done') runComputeR()
  }
}

// --- File Handlers ---
const onCNdviChange = (e) => { cNdviFile.value = e.target.files?.[0] ?? null }
const onCShpChange = (e) => { cShpZip.value = e.target.files?.[0] ?? null }

const onKRasterChange = (e) => { kRasterFile.value = e.target.files?.[0] ?? null }
const onKAttributeChange = (e) => { kAttributeFile.value = e.target.files?.[0] ?? null }
const onKShpChange = (e) => { kShpZip.value = e.target.files?.[0] ?? null }

const onLSDemChange = (e) => { lsDemFile.value = e.target.files?.[0] ?? null }

const onPCategoryChange = (e) => { pCategoryFile.value = e.target.files?.[0] ?? null }

const onRYearsChange = (e) => { rYearsFiles.value = e.target.files }
const onRShpChange = (e) => { rShpZip.value = e.target.files?.[0] ?? null }

const goHome = () => {
  router.push({ name: 'home' })
}

// --- API Calls ---

const runComputeC = async () => {
  if (!cNdviFile.value || !cShpZip.value) {
    errorMessage.value = '请上传 NDVI 和范围 ZIP 文件'
    return
  }
  cStatus.value = 'running'
  cResult.value = null
  cPreviewUrl.value = ''
  
  try {
    const fd = new FormData()
    fd.append('ndvi_file', cNdviFile.value)
    fd.append('shp_zip', cShpZip.value)
    
    const res = await fetch(`${BASE_URL}c-factor`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`请求失败: ${res.statusText}`)
    
    const data = await res.json()
    cResult.value = {
      mainUrl: normalizeUrl(data.c_tif_url),
      mainName: 'C_Factor.tif',
      visUrl: normalizeUrl(data.visualization_url),
      reportUrl: normalizeUrl(data.report_url),
      stats: data.c_stats
    }
    // C factor returns a visualization PNG, use it directly
    cPreviewUrl.value = normalizeUrl(data.visualization_url)
    cStatus.value = 'done'
  } catch (e) {
    console.error(e)
    errorMessage.value = '计算失败: ' + e.message
    cStatus.value = 'idle'
  }
}

const runComputeK = async () => {
  if (!kRasterFile.value || !kShpZip.value || !kAttributeFile.value) {
    errorMessage.value = '请上传栅格、属性表和范围 ZIP 文件'
    return
  }
  kStatus.value = 'running'
  kResult.value = null
  kPreviewUrl.value = ''
  
  try {
    const fd = new FormData()
    fd.append('raster_file', kRasterFile.value)
    fd.append('shp_zip', kShpZip.value)
    fd.append('attribute_xls', kAttributeFile.value)
    
    const res = await fetch(`${BASE_URL}k-factor`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`请求失败: ${res.statusText}`)
    
    const data = await res.json()
    kResult.value = {
      mainUrl: normalizeUrl(data.k_tif_url),
      mainName: 'K_Factor.tif',
      csvUrl: normalizeUrl(data.k_values_csv_url),
      stats: data.k_stats
    }
    
    // Render TIFF preview
    const tifBlob = await fetch(normalizeUrl(data.k_tif_url)).then(r => r.blob())
    kPreviewUrl.value = await renderTiffToDataUrl(tifBlob)
    kStatus.value = 'done'
  } catch (e) {
    console.error(e)
    errorMessage.value = '计算失败: ' + e.message
    kStatus.value = 'idle'
  }
}

const runComputeLS = async () => {
  if (!lsDemFile.value) {
    errorMessage.value = '请上传 DEM 文件'
    return
  }
  lsStatus.value = 'running'
  lsResult.value = null
  lsPreviewUrl.value = ''
  
  try {
    const fd = new FormData()
    fd.append('dem_file', lsDemFile.value)
    if (lsTargetResolution.value) fd.append('target_resolution', lsTargetResolution.value)
    if (lsResampleMethod.value) fd.append('resample_method', lsResampleMethod.value)
    if (lsChunkSize.value) fd.append('chunk_size', lsChunkSize.value)
    
    const res = await fetch(`${BASE_URL}ls-factor`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`请求失败: ${res.statusText}`)
    
    const data = await res.json()
    lsResult.value = {
      mainUrl: normalizeUrl(data.ls_tif_url),
      mainName: 'LS_Factor.tif',
      reportUrl: normalizeUrl(data.log_url),
      stats: data.ls_stats
    }
    
    const tifBlob = await fetch(normalizeUrl(data.ls_tif_url)).then(r => r.blob())
    lsPreviewUrl.value = await renderTiffToDataUrl(tifBlob)
    lsStatus.value = 'done'
  } catch (e) {
    console.error(e)
    errorMessage.value = '计算失败: ' + e.message
    lsStatus.value = 'idle'
  }
}

const runPrepareP = async () => {
  if (!pCategoryFile.value) {
    errorMessage.value = '请上传分类栅格 ZIP'
    return
  }
  pStatus.value = 'preparing'
  pValues.value = []
  pMapping.value = {}
  
  try {
    const fd = new FormData()
    fd.append('category_tif', pCategoryFile.value)
    
    const res = await fetch(`${BASE_URL}p-factor/prepare`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`请求失败: ${res.statusText}`)
    
    const data = await res.json()
    if (data.values && Array.isArray(data.values)) {
      pValues.value = data.values.sort((a, b) => a - b)
      // Initialize mapping with defaults? No, empty.
    }
    pStatus.value = 'prepared'
  } catch (e) {
    console.error(e)
    errorMessage.value = '解析失败: ' + e.message
    pStatus.value = 'idle'
  }
}

const runApplyP = async () => {
  if (!pCategoryFile.value) {
    errorMessage.value = '文件丢失，请重新上传'
    pStatus.value = 'idle'
    return
  }
  
  // Validate mapping
  const mapping = { ...pMapping.value }
  // Ensure all values are numbers
  for (const k in mapping) {
    mapping[k] = parseFloat(mapping[k])
  }
  
  pStatus.value = 'applying'
  pResult.value = null
  pPreviewUrl.value = ''
  
  try {
    const fd = new FormData()
    fd.append('category_tif', pCategoryFile.value)
    fd.append('value_p_mapping', JSON.stringify(mapping))
    
    const res = await fetch(`${BASE_URL}p-factor/apply`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`请求失败: ${res.statusText}`)
    
    const data = await res.json()
    pResult.value = {
      mainUrl: normalizeUrl(data.p_tif_url),
      mainName: 'P_Factor.tif',
      visUrl: data.attributes_zip_url ? normalizeUrl(data.attributes_zip_url) : null
    }
    
    const tifBlob = await fetch(normalizeUrl(data.p_tif_url)).then(r => r.blob())
    pPreviewUrl.value = await renderTiffToDataUrl(tifBlob)
    pStatus.value = 'done'
  } catch (e) {
    console.error(e)
    errorMessage.value = '计算失败: ' + e.message
    pStatus.value = 'prepared' // Back to prepared state
  }
}

const runComputeR = async () => {
  if (!rYearsFiles.value || rYearsFiles.value.length === 0 || !rShpZip.value) {
    errorMessage.value = '请上传年份数据 ZIP 和范围 ZIP'
    return
  }
  rStatus.value = 'running'
  rResult.value = null
  rPreviewUrl.value = ''
  
  try {
    const fd = new FormData()
    for (let i = 0; i < rYearsFiles.value.length; i++) {
      fd.append('years_zip', rYearsFiles.value[i])
    }
    fd.append('shp_zip', rShpZip.value)
    fd.append('scale_factor', rScaleFactor.value)
    
    const res = await fetch(`${BASE_URL}r-factor`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`请求失败: ${res.statusText}`)
    
    const data = await res.json()
    rResult.value = {
      mainUrl: normalizeUrl(data.r_tif_url),
      mainName: 'R_Factor.tif',
      yearsUrls: data.years_zip_url ? data.years_zip_url.map(normalizeUrl) : [],
      shpUrl: data.shp_zip_url ? normalizeUrl(data.shp_zip_url) : null,
      stats: data.r_stats
    }
    
    const tifBlob = await fetch(normalizeUrl(data.r_tif_url)).then(r => r.blob())
    rPreviewUrl.value = await renderTiffToDataUrl(tifBlob)
    rStatus.value = 'done'
  } catch (e) {
    console.error(e)
    errorMessage.value = '计算失败: ' + e.message
    rStatus.value = 'idle'
  }
}

// --- Tiff Rendering (Copied/Adapted from Bhwytj.vue) ---
const renderTiffToDataUrl = async (blob) => {
  try {
    const arrayBuffer = await blob.arrayBuffer()
    const ifds = decode(arrayBuffer)
    if (!ifds || ifds.length === 0) return ''
    
    const ifd = ifds[0]
    const { width, height, data } = ifd
    const totalPixels = width * height
    // Simple estimation: data.length / totalPixels
    // However, data might be typed array. 
    // If float32, data.length is pixels. 
    // ifd.samplesPerPixel is reliable.
    const channels = ifd.samplesPerPixel || (data.length / totalPixels)
    
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    const imageData = ctx.createImageData(width, height)
    const output = imageData.data
    
    if (channels === 1) {
      // Find min/max for normalization
      let min = Infinity, max = -Infinity
      // Handle TypedArray
      for (let i = 0; i < totalPixels; i++) {
        const val = data[i]
        if (val < min) min = val
        if (val > max) max = val
      }
      const range = max - min || 1
      
      for (let i = 0; i < totalPixels; i++) {
        const val = data[i]
        // Simple linear stretch
        const norm = Math.floor(((val - min) / range) * 255)
        const pos = i * 4
        output[pos] = norm
        output[pos + 1] = norm
        output[pos + 2] = norm
        output[pos + 3] = 255
      }
    } else {
      // Assume RGB(A) or similar
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
</script>

<style scoped>
/* No specific styles needed beyond Tailwind */
</style>