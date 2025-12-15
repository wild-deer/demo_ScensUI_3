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
        坡面物源体积
      </div>
    </header>

    <div class="flex flex-1 p-4 gap-4">
      <aside class="w-80 max-w-[28rem] flex-shrink-0 rounded-lg border border-gray-200 bg-gray-100 p-4 text-slate-900">
        <div class="mb-3 text-sm font-semibold text-slate-700">子功能</div>
        <div class="flex gap-2 mb-4 text-[12px]">
          <button @click="activeTab = 'c'" :class="tabClass('c')">C 因子</button>
          <button @click="activeTab = 'k'" :class="tabClass('k')">K 因子</button>
          <button @click="activeTab = 'ls'" :class="tabClass('ls')">LS 因子</button>
          <button @click="activeTab = 'p'" :class="tabClass('p')">P 因子</button>
          <button @click="activeTab = 'r'" :class="tabClass('r')">R 因子</button>
        </div>

        <div class="mb-3 text-lg font-bold text-slate-700 pb-2">输入文件</div>
        <div v-if="activeTab === 'c'" class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">NDVI 文件</label>
            <input type="file" accept=".tif,.img,.nc,.hdf" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onCNdviChange" />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">SHP 文件</label>
            <input type="file" accept=".shp,.shx,.dbf,.prj" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onCShpChange" />
          </div>
        </div>

        <div v-else-if="activeTab === 'k'" class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">HWSD 栅格（.bil）</label>
            <input type="file" accept=".bil" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onKBilChange" />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">HWSD 元数据（.data）</label>
            <input type="file" accept=".data,.txt,.csv" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onKDataChange" />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">SHP 文件</label>
            <input type="file" accept=".shp,.shx,.dbf,.prj" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onKShpChange" />
          </div>
        </div>

        <div v-else-if="activeTab === 'ls'" class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">DEM</label>
            <input type="file" accept=".tif,.dem,.asc" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onLSDemChange" />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">采样分辨率（可选）</label>
            <input v-model="lsResolution" type="number" min="1" step="1" placeholder="不输入则不重采样" class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <div v-else-if="activeTab === 'p'" class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">DEM</label>
            <input type="file" accept=".tif,.dem,.asc" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onPDemChange" />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">P 值</label>
            <input v-model.number="pValue" type="number" min="0" step="0.01" placeholder="例如：0.5" class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <div v-else class="space-y-4">
          <div>
            <label class="block text-sm mb-2 text-slate-700">降雨量数据文件（可多选）</label>
            <input type="file" multiple accept=".csv,.txt,.xlsx,.json" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onRFilesChange" />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">缩放参数</label>
            <input v-model.number="rScale" type="number" min="0" step="0.01" placeholder="例如：1.0" class="w-full px-3 py-2 rounded-md bg-gray-100 border border-gray-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="block text-sm mb-2 text-slate-700">SHP 文件</label>
            <input type="file" accept=".shp,.shx,.dbf,.prj" class="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700" @change="onRShpChange" />
          </div>
        </div>

        <div class="mt-6 pt-6">
          <div class="mb-3 text-lg font-bold text-slate-700 py-2">输出文件</div>
          <div v-if="currentStatus === 'done'" class="mt-2 space-y-2">
            <div class="text-sm">计算完成</div>
            <a v-if="currentResult.fileUrl" :href="currentResult.fileUrl" :download="currentResult.fileName" class="inline-block px-3 py-2 rounded-md bg-green-600 text-white hover:bg-green-700">下载结果文件</a>
          </div>
        </div>
        <div class="pt-6">
          <button
            class="w-full py-2 rounded-md transition"
            :class="currentStatus === 'running' ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[.99]'"
            :disabled="currentStatus === 'running'"
            @click="onActionClick"
          >
            {{ buttonText }}
          </button>
        </div>
      </aside>

      <main class="flex-1 rounded-lg border border-gray-200 bg-gray-100 overflow-hidden grid place-items-center">
        <img v-if="currentPreviewUrl" :src="currentPreviewUrl" class="max-w-full max-h-full object-contain" />
      </main>
    </div>
  </div>
  </template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('c')

// C 因子
const cNdviFile = ref(null)
const cShpFile = ref(null)
const cStatus = ref('idle')
const cResult = ref({ fileUrl: '', fileName: 'c_factor_result.tif' })
const cPreviewUrl = ref('')

// K 因子
const kBilFile = ref(null)
const kDataFile = ref(null)
const kShpFile = ref(null)
const kStatus = ref('idle')
const kResult = ref({ fileUrl: '', fileName: 'k_factor_result.tif' })
const kPreviewUrl = ref('')

// LS 因子
const lsDemFile = ref(null)
const lsResolution = ref(null)
const lsStatus = ref('idle')
const lsResult = ref({ fileUrl: '', fileName: 'ls_factor_result.tif' })
const lsPreviewUrl = ref('')

// P 因子
const pDemFile = ref(null)
const pValue = ref(0.5)
const pStatus = ref('idle')
const pResult = ref({ fileUrl: '', fileName: 'p_factor_result.tif' })
const pPreviewUrl = ref('')

// R 因子
const rFiles = ref(null)
const rScale = ref(1.0)
const rShpFile = ref(null)
const rStatus = ref('idle')
const rResult = ref({ fileUrl: '', fileName: 'r_factor_result.tif' })
const rPreviewUrl = ref('')

const tabClass = (key) =>
  activeTab.value === key
    ? 'px-3 py-2 rounded-md bg-blue-600 text-white'
    : 'px-3 py-2 rounded-md bg-gray-200 text-slate-900 hover:bg-gray-300'

const buttonText = computed(() => {
  if (currentStatus.value === 'running') return '正在计算'
  if (currentStatus.value === 'done') return '重新计算'
  return '开始计算'
})

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

const onActionClick = () => {
  if (activeTab.value === 'c') {
    if (cStatus.value === 'idle') runComputeC()
    else if (cStatus.value === 'done') { cStatus.value = 'idle'; cResult.value = { fileUrl: '', fileName: 'c_factor_result.tif' }; cPreviewUrl.value = ''; runComputeC() }
  } else if (activeTab.value === 'k') {
    if (kStatus.value === 'idle') runComputeK()
    else if (kStatus.value === 'done') { kStatus.value = 'idle'; kResult.value = { fileUrl: '', fileName: 'k_factor_result.tif' }; kPreviewUrl.value = ''; runComputeK() }
  } else if (activeTab.value === 'ls') {
    if (lsStatus.value === 'idle') runComputeLS()
    else if (lsStatus.value === 'done') { lsStatus.value = 'idle'; lsResult.value = { fileUrl: '', fileName: 'ls_factor_result.tif' }; lsPreviewUrl.value = ''; runComputeLS() }
  } else if (activeTab.value === 'p') {
    if (pStatus.value === 'idle') runComputeP()
    else if (pStatus.value === 'done') { pStatus.value = 'idle'; pResult.value = { fileUrl: '', fileName: 'p_factor_result.tif' }; pPreviewUrl.value = ''; runComputeP() }
  } else {
    if (rStatus.value === 'idle') runComputeR()
    else if (rStatus.value === 'done') { rStatus.value = 'idle'; rResult.value = { fileUrl: '', fileName: 'r_factor_result.tif' }; rPreviewUrl.value = ''; runComputeR() }
  }
}

const runComputeC = () => {
  cStatus.value = 'running'
  setTimeout(() => {
    const blob = new Blob(['CFACTOR'], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    cResult.value = { fileUrl: url, fileName: 'c_factor_result.tif' }
    cPreviewUrl.value = createPreview('c')
    cStatus.value = 'done'
  }, 1000)
}
const runComputeK = () => {
  kStatus.value = 'running'
  setTimeout(() => {
    const blob = new Blob(['KFACTOR'], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    kResult.value = { fileUrl: url, fileName: 'k_factor_result.tif' }
    kPreviewUrl.value = createPreview('k')
    kStatus.value = 'done'
  }, 1000)
}
const runComputeLS = () => {
  lsStatus.value = 'running'
  setTimeout(() => {
    const blob = new Blob(['LSFACTOR'], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    lsResult.value = { fileUrl: url, fileName: 'ls_factor_result.tif' }
    lsPreviewUrl.value = createPreview('ls')
    lsStatus.value = 'done'
  }, 1000)
}
const runComputeP = () => {
  pStatus.value = 'running'
  setTimeout(() => {
    const blob = new Blob(['PFACTOR'], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    pResult.value = { fileUrl: url, fileName: 'p_factor_result.tif' }
    pPreviewUrl.value = createPreview('p')
    pStatus.value = 'done'
  }, 1000)
}
const runComputeR = () => {
  rStatus.value = 'running'
  setTimeout(() => {
    const blob = new Blob(['RFACTOR'], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    rResult.value = { fileUrl: url, fileName: 'r_factor_result.tif' }
    rPreviewUrl.value = createPreview('r')
    rStatus.value = 'done'
  }, 1000)
}

const onCNdviChange = (e) => { cNdviFile.value = e.target.files?.[0] ?? null }
const onCShpChange = (e) => { cShpFile.value = e.target.files?.[0] ?? null }
const onKBilChange = (e) => { kBilFile.value = e.target.files?.[0] ?? null }
const onKDataChange = (e) => { kDataFile.value = e.target.files?.[0] ?? null }
const onKShpChange = (e) => { kShpFile.value = e.target.files?.[0] ?? null }
const onLSDemChange = (e) => { lsDemFile.value = e.target.files?.[0] ?? null }
const onPDemChange = (e) => { pDemFile.value = e.target.files?.[0] ?? null }
const onRFilesChange = (e) => { rFiles.value = e.target.files }
const onRShpChange = (e) => { rShpFile.value = e.target.files?.[0] ?? null }

const goHome = () => {
  router.push({ name: 'home' })
}

const createPreview = (type) => {
  const c = document.createElement('canvas')
  c.width = 640
  c.height = 360
  const ctx = c.getContext('2d')
  const grad = ctx.createLinearGradient(0, 0, c.width, c.height)
  const colors = {
    c: ['#1e3a8a', '#93c5fd'],
    k: ['#7c3aed', '#c4b5fd'],
    ls: ['#065f46', '#34d399'],
    p: ['#b91c1c', '#fecaca'],
    r: ['#92400e', '#fbbf24'],
  }[type]
  grad.addColorStop(0, colors[0])
  grad.addColorStop(1, colors[1])
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, c.width, c.height)
  return c.toDataURL('image/png')
}
</script>

<style scoped>
</style>
