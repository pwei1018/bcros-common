<script setup lang="ts">
import { truncate } from "~/utils/documentRecords"
const {
  downloadFileFromUrl,
} = useDocuments()

defineProps({
  downloadUrl: {
    type: String,
    required: false,
    default: ''
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
        v-if="fileName.length > 15"
        :popper="{ placement: 'bottom' }"
        :text="fileName"
      >
      <img class="w-5 h-5 mr-1.5" src="~/assets/icons/pdf_download.svg" alt="pdf download">
      {{ truncate(fileName, 15, 6, 6) }}
      </UTooltip>
      <template v-else>
        <img class="w-5 h-5 mr-1.5" src="~/assets/icons/pdf_download.svg" alt="pdf download">
        {{ fileName }}
      </template>
  </ULink>
</template>