<script setup lang="ts">
defineProps({
  name: {
    type: String,
    required: true,
  },
  isTable: {
    type: Boolean,
    required: false,
  }
})
</script>
<template>
  <div :data-cy="'content_wrapper_' + name">
    <div
      :data-cy="'header_' + name"
      :class="
        isTable
          ? 'font-bold text-gray-900 bg-bcGovColor-ltBlue px-5 py-[18px]'
          : 'font-bold text-gray-900 bg-bcGovColor-ltBlue px-8 py-[18px]'
      "
    >
      <slot name="header" />
    </div>
    <div
      :data-cy="'content_' + name"
      :class="
        isTable ? 'bg-white rounded pb-0' : 'bg-white rounded px-8 pt-8 pb-0'
      "
    >
      <slot name="content" />
    </div>
  </div>
</template>
