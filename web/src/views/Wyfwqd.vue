<template>
  <div class="flex flex-col h-screen w-screen text-center text-white inset-0 m-0 p-0 overflow-auto bg-cover bg-center">
    <!-- 顶部标题 -->

    <!-- 主内容区 -->
    <div class="flex flex-1">
      <!-- 左侧边栏 -->
      <div class="w-1/6 items-center justify-center select-none hidden lg:block"></div>

      <!-- 中间内容 -->
      <div class="flex-1 lg:p-4">
        <div class="flex flex-col">
          <div class="flex-1 flex flex-col items-center">
            <ul class="menu menu-horizontal bg-blue-500 flex w-full h-20 items-center">
              <li @click="() => navigateToSourceRange('home')">
                <a class="tooltip" data-tip="返回主界面">
                  <svg t="1746861798350" class="icon w-10 h-10" viewBox="0 0 1024 1024" version="1.1"
                    xmlns="http://www.w3.org/2000/svg" p-id="4247" width="200" height="200">
                    <path
                      d="M507.264 128L583.04 203.84 274.944 512l308.16 308.16L507.264 896 128 516.736 132.736 512 128 507.264 507.264 128z m320 0l75.84 75.84L594.944 512l308.16 308.16L827.264 896 448 516.736 452.736 512 448 507.264 827.264 128z"
                      p-id="4248"></path>
                  </svg>
                </a>
              </li>

              <div class="flex-2/3 text-2xl select-none">物源范围圈定</div>
              <label class="flex cursor-pointer gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
                <input type="checkbox" value="light" class="toggle theme-controller" />
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="5" />
                  <path
                    d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
                </svg>
              </label>
            </ul>
            <!-- 占位元素 -->
            <!-- <div class="h-10"></div> -->
            <div class="w-full min-h-200 lg:min-h-200 bg-base-200 select-none" >
              <div class="w-full overflow-auto flex flex-row bg-base-200">
                <div class="flex-1/8  select-none"></div>

  <fieldset class="fieldset bg-base-200 border-base-300 rounded-box w-xs border p-4  ">
  <legend class="fieldset-legend select-none">Page details</legend>

  <label class="label select-none">Title</label>

    <input type="file" class="file-input text-base-content" @change="handleFileUpload" ref="fileInput" />
    <button class="btn" @click="submitFile" :disabled="!selectedFile">上传文件</button>
    <div v-if="uploading">上传中...</div>
    <div v-if="errorMessage">{{ errorMessage }}</div>
    <div v-if="successMessage">{{ successMessage }}</div>
  <label class="label">Slug</label>
  <input type="text" class="input" placeholder="my-awesome-page" />

  <label class="label">Author</label>
  <input type="text" class="input" placeholder="Name" />
</fieldset>

                <div class="flex-1/8 select-none "></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧边栏 -->
      <div class="w-1/6 hidden lg:block items-center justify-center select-none"></div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ref } from 'vue'
const fileInput = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
// 处理文件选择
const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    errorMessage.value = ''
    successMessage.value = ''
  }
}

// 提交文件到服务器
const submitFile = async () => {
  if (!selectedFile.value) return
  
  uploading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    // 创建FormData对象
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    // 其他可能需要的表单字段
    formData.append('fileName', selectedFile.value.name)
    formData.append('uploadTime', new Date().toISOString())
    
    // 发送Fetch请求
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData,
      // 注意：不要设置Content-Type头，让浏览器自动设置
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`)
    }
    
    const result = await response.json()
    successMessage.value = '文件上传成功!'
    console.log('上传成功:', result)
    
    // 重置文件输入
    fileInput.value.value = ''
    selectedFile.value = null
  } catch (error) {
    errorMessage.value = '上传失败: ' + error.message
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}
// 组件逻辑可以直接写在这里
const router = useRouter()
const navigateToSourceRange = (param, event) => {
  console.log('参数:', param) // 输出: "参数值"
  console.log('事件对象:', event) // 原生 DOM 事件
  // 方式2：通过动态路由参数传递（需在路由配置中定义 path: '/source-range/:param'）
  router.push({
    name: param,
  })
}
</script>

<style scoped>
/* 引入 Font Awesome 图标库 */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css');
</style>
