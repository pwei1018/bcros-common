<script setup lang="ts">
const route = useRoute()
const {
  documentRecord,
  isEditingReview
} = storeToRefs(useBcrosDocuments())
const crumbConstructors = computed(() => (route?.meta?.breadcrumbs || []) as (() => BreadcrumbI)[])

</script>
<template>
  <div
    class="app-container"
    data-cy="tombstone-footer"
  >
    <BcrosHeader />
    <BcrosBreadcrumb v-if="crumbConstructors.length" :crumb-constructors="crumbConstructors" />
    <Tombstone
      v-if="documentRecord?.consumerDocumentId && !isEditingReview"
      :tombstone-title="$t('documentReview.labels.documentId') + ' ' + documentRecord?.consumerDocumentId"
    />
    <slot />
    <BcrosFooter />
  </div>
</template>