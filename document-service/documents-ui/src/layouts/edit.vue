<script setup lang="ts">
const { isEditing } = storeToRefs(useBcrosDocuments())
const route = useRoute()
const crumbConstructors = computed(() => (route?.meta?.breadcrumbs || []) as (() => BreadcrumbI)[])
</script>
<template>
  <div
    class="app-container"
    data-cy="tombstone-footer"
  >
    <BcrosHeader />
    <BcrosBreadcrumb v-if="crumbConstructors.length" :crumb-constructors="crumbConstructors" />
    <Tombstone />
    <div class="app-inner-container app-body">
      <slot />
    </div>
    <NavFooter
      v-if="isEditing"
      cancel-btn="Cancel"
      :next-btn="'Review and Confirm'"
      @cancel="isEditing = false"
      @next="console.log('next')"
    />
    <BcrosFooter />
  </div>
</template>