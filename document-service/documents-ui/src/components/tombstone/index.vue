<script setup lang="ts">
defineProps({
  tombstoneTitle: {
    type: String,
    default: 'Tombstone Default Title'
  }
})
</script>
<template>
  <div
    data-cy="tombstone"
    class="w-full bg-white"
  >
    <div
      v-if="tombstoneTitle"
      class="app-inner-container h-[100px] content-center"
    >
      <span class="text-[22px] font-bold text-gray-900">{{ tombstoneTitle }}</span>
    </div>
  </div>
</template>