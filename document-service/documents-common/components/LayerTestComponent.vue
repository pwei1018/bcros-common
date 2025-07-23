<template>
  <div class="container bg-white p-4">
    <h2>Playground Test Component</h2>
    <p>{{ message }}</p>
    <UButton @click="handleClick">Toggle Me</UButton>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const toggled = ref(false)
const message = ref('Hello from PlaygroundTest!')
function handleClick() {
  toggled.value = !toggled.value
  message.value = toggled.value
    ? 'You toggled a button, yay!'
    : 'Hello from PlaygroundTest!'
}
</script>
