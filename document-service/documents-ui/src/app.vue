<script setup lang="ts">
const { isLoading } = storeToRefs(useBcrosDocuments())
</script>
<template>
    <NuxtLayout class="bg-bcGovGray-100">
      <!-- Loading Overlay and Spinner -->
      <template v-if="isLoading">
        <div class="fixed left-0 top-0 h-full w-full z-50 bg-gray-300 opacity-45" />
        <UIcon
          name="i-mdi-loading"
          class="animate-spin text-[50px] text-blue-500 absolute top-40 left-[50%]"
        />
      </template>

      <NuxtPage />
    </NuxtLayout>
</template>