<script setup lang="ts">
defineProps({
  tombstoneTitle: {
    type: String,
    default: 'Tombstone Default Title'
  }
})
const { documentRecord } = storeToRefs(useBcrosDocuments())
</script>
<template>
  <div
    data-cy="tombstone"
    class="w-full bg-white"
  >
    <div class="app-inner-container h-[100px] content-center">
      <span class="text-[22px] font-bold text-gray-900">
        {{ $t('documentReview.labels.documentId') + ' ' + documentRecord.consumerDocumentId }}
      </span>
    </div>
  </div>
</template>