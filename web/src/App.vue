<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

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
</script>

<template>
  <div
    class="fixed inset-0 w-full h-full m-0 p-0 overflow-hidden bg-gray-100 bg-cover bg-center bg-[url('/src/assets/background.png')]"
  >
    <Transition :name="transitionName" mode="out-in">
      <RouterView />
    </Transition>
  </div>
</template>

<style scoped>
/* 路由左滑动画（前进） */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.5s ease;
  position: absolute;
  width: 100%;
  height: 100%;
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

/* 路由右滑动画（后退） */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.5s ease;
  position: absolute;
  width: 100%;
  height: 100%;
}

.slide-right-enter-from {
  transform: translateX(-100%);
  opacity: 0;
}

.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
