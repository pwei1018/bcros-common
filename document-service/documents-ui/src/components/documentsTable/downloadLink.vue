<script setup lang="ts">
import { truncate } from "~/utils/documentRecords"
const {
  downloadFileFromUrl,
} = useDocuments()

defineProps({
  downloadUrl: {
    type: String,
    required: true
  },
  fileName: {
    type: String,
    required: true
  }
})

</script>
<template>
  <ULink
    inactive-class="text-primary"
    class="flex align-center"
    @click="downloadFileFromUrl(downloadUrl, fileName)"
  >
      <UTooltip
        :popper="{ placement: 'bottom' }"
        :text="fileName"
      >
      <UIcon name="i-mdi-file-download" class="w-5 h-5" />
      {{ truncate(fileName, 15, 6, 6) }}
      </UTooltip>
  </ULink>
</template>