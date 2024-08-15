<script setup lang="ts">
defineProps({
  name: {
    type: String,
    required: true
  }
})
</script>
<template>
  <div :data-cy="'content_wrapper_' + name">
    <div
      :data-cy="'header_' + name"
      class="font-bold text-gray-900 bg-bcGovColor-ltBlue h-[60px] px-6 pt-[18px]"
    >
      <slot name="header" />
    </div>
    <div
      :data-cy="'content_' + name"
      class="bg-white rounded px-6 pt-8 pb-0"
    >
      <slot name="content" />
    </div>
  </div>
</template>