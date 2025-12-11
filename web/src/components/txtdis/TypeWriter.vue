<template>
  <div class="inline-block min-w-[2ch]">
    <h1
      class="text-4xl md:text-5xl font-bold relative"
      :class="{ 'typing-animation': isTyping, 'cursor-blink': isBlinking }"
    >
      {{ displayText }}
      <!-- <span v-if="isBlinking" class="cursor">|</span> -->
    </h1>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue'

const props = defineProps({
  text: {
    type: String,
    required: true,
  },
  typingSpeed: {
    type: Number,
    default: 50,
  },
  cursorColor: {
    type: String,
    default: '#000',
  },
  startOnMount: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['typing-complete'])

const displayText = ref('')
const isTyping = ref(false)
const isBlinking = ref(true)
let typingTimer = null

const resetTyping = () => {
  clearInterval(typingTimer)
  displayText.value = ''
  isTyping.value = false
  isBlinking.value = true
}

const typeText = () => {
  resetTyping()
  isTyping.value = true

  let i = 0
  typingTimer = setInterval(() => {
    if (i <= props.text.length) {
      displayText.value = props.text.substring(0, i)
      i++
    } else {
      clearInterval(typingTimer)
      isTyping.value = false
      emit('typing-complete')
    }
  }, props.typingSpeed)
}

onMounted(() => {
  if (props.startOnMount) {
    nextTick(() => {
      typeText()
    })
  }
})

watch(
  () => props.text,
  (newText) => {
    if (newText !== displayText.value) {
      typeText()
    }
  },
)

onUnmounted(() => {
  clearInterval(typingTimer)
})
</script>

<style scoped>
.typing-animation::after {
  content: '';
  position: absolute;
  height: 100%;
  width: 2px;
  background-color: currentColor;
  animation: blink 0.7s;
  margin-left: 2px;
}

.cursor-blink .cursor {
  animation: blink 0.7s;
  color: v-bind('props.cursorColor');
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
</style>
