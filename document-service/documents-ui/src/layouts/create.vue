<script setup lang="ts">
const route = useRoute()
const { isValidIndexData, saveDocuments, scrollToFirstError } = useDocuments()
const { validateIndex } = storeToRefs(useBcrosDocuments())
const crumbConstructors = computed(() => (route?.meta?.breadcrumbs || []) as (() => BreadcrumbI)[])
const isReview = computed(() => route.name === RouteNameE.DOCUMENT_INDEXING_REVIEW)
const cancel = async () => await navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
const back = async () => await navigateTo({ name: RouteNameE.DOCUMENT_INDEXING })
const next = async () => {
  // Validate Indexing Form
  validateIndex.value = true
  await nextTick()
  scrollToFirstError()
  if (!isValidIndexData.value) return

  isReview.value
    ? await saveDocuments().then(() => navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT }))
    : await navigateTo({ name: RouteNameE.DOCUMENT_INDEXING_REVIEW })
}

</script>
<template>
  <div class="app-container" data-cy="default-layout">
    <bcros-header />
    <bcros-breadcrumb v-if="crumbConstructors.length" :crumb-constructors="crumbConstructors" />
    <div class="app-inner-container app-body">
      <slot />
    </div>
    <NavFooter
      cancel-btn="Cancel"
      :next-btn="isReview ? 'Save Record' : 'Review and Confirm'"
      :back-btn="isReview ? 'Back' : ''"
      @cancel="cancel"
      @back="back"
      @next="next"
    />
    <bcros-footer />
  </div>
</template>