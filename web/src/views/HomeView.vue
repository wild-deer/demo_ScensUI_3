<template>
  <div class="h-full w-full flex items-center justify-center">
    <div class="text-center">
      <TypeWriter
        :text="'岩体结构面识别与稳定性快速评价系统'"
        :typingSpeed="66"
        class="text-4xl font-bold text-blue-600 mb-8 select-none"
      />
      <div class="text-gray-500 text-xl mb-6">
        请从左侧菜单选择功能模块开始使用
      </div>
      <div class="flex gap-4 justify-center">
        <router-link
          to="/icon-gallery"
          class="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-lg font-medium"
        >
          查看图标库
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import TypeWriter from '@/components/txtdis/TypeWriter.vue'
</script>

<style scoped>
/* 引入 Font Awesome 图标库 */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css');
</style>
