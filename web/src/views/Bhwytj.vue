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
            <div>体积结果：<span class="font-mono">{{ result.value }}</span></div>
            <a
              v-if="result.fileUrl"
              :href="result.fileUrl"
              :download="result.fileName"
              class="inline-block px-3 py-2 rounded-md bg-green-600 text-white hover:bg-green-700"
            >
              下载结果文件
            </a>
          </div>
        </div>
        <div class="pt-10">
          <button
            class="w-full py-2 rounded-md transition"
            :class="status === 'running' ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[.99]'"
            :disabled="status === 'running'"
            @click="onActionClick"
          >
            {{ buttonText }}
          </button>
        </div>
      </aside>

      <main class="flex-1 rounded-lg border border-gray-200 bg-gray-100 overflow-hidden grid place-items-center">
        <img v-if="previewUrl" :src="previewUrl" class="max-w-full max-h-full object-contain" />
      </main>
    </div>
  </div>
  </template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const demFile = ref(null)
const iterations = ref(10)

const status = ref('idle')
const result = ref({ value: null, fileUrl: '', fileName: 'bh_volume_result.json' })
const previewUrl = ref('')

const buttonText = computed(() => {
  if (status.value === 'running') return '正在计算'
  if (status.value === 'done') return '重新计算'
  return '开始计算'
})

const runCompute = () => {
  status.value = 'running'
  setTimeout(() => {
    const volume = Math.round(Math.random() * 100000) / 10
    const blob = new Blob([JSON.stringify({ volume, iterations: iterations.value })], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    result.value = { value: volume, fileUrl: url, fileName: 'bh_volume_result.json' }
    previewUrl.value = createPreview(volume)
    status.value = 'done'
  }, 1200)
}

const onActionClick = () => {
  if (status.value === 'idle') {
    runCompute()
  } else if (status.value === 'done') {
    status.value = 'idle'
    result.value = { value: null, fileUrl: '', fileName: 'bh_volume_result.json' }
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

<style scoped>
</style>
