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
        v-if="fileName.length > 15"
        :popper="{ placement: 'bottom' }"
        :text="fileName"
      >
      <UIcon name="i-mdi-file-download mr-1.5" class="w-5 h-5" />
      {{ truncate(fileName, 15, 6, 6) }}
      </UTooltip>
      <template v-else>
        <UIcon name="i-mdi-file-download mr-1.5" class="w-5 h-5" />
        {{ fileName }}
      </template>
  </ULink>
</template>