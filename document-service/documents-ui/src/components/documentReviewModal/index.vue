<script setup lang="ts">
import { formatToReadableDate } from '../../utils/dateHelper'

const { displayDocumentReview, documentInfoRO } = storeToRefs(useBcrosDocuments())
const loadingDocuments = ref(false)

const requestDocumentRecord = async (consumerId: string) => {
  loadingDocuments.value = true
  await getDocumentRecord(consumerId)
  loadingDocuments.value = false
  navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
}
</script>

<template>
  <UModal v-model="displayDocumentReview" :data-cy="'document-review-modal'" prevent-close>
    <div class="px-6 py-6">
      <div class="flex flex-row-reverse">
        <UButton
          icon="i-mdi-close"
          size="md"
          color="primary"
          variant="ghost"
          :disabled="loadingDocuments"
          @click="displayDocumentReview = false"
        />
      </div>

      <div class="pr-4">
        <div class="flex flex-row -mt-4">
          <h3 class="text-[24px] font-bold">Document Information Saved</h3>
        </div>

        <div class="flex flex-row py-6">
          <span class="text-gray-700 font-normal text-[16px] leading-6">Your document information has been successfully
            uploaded and saved. To view, complete a search on the document management page using the following
            information
          </span>
        </div>

        <div class="grid grid-flow-row auto-rows-max">
          <div>
            <span class="font-bold">Document ID: </span>
            <span class="px-1">{{ documentInfoRO.consumerDocumentId }}</span>
          </div>
          <div>
            <span class="font-bold">Entity ID: </span>
            <span class="px-1">{{ documentInfoRO.consumerIdentifier || 'Not Entered' }}</span>
          </div>
          <div>
            <span class="font-bold">Document Category: </span>
            <span class="px-1">{{ documentInfoRO.documentClass }}</span>
          </div>
          <div>
            <span class="font-bold">Document Type: </span>
            <span class="px-1">{{ documentInfoRO.documentType }}</span>
          </div>
          <div>
            <span class="font-bold">Filing Date: </span>
            <span class="px-1">{{ formatToReadableDate(documentInfoRO.consumerFilingDateTime) || 'Not Entered' }}</span>
          </div>

          <div class="pt-8">
            <span class="font-bold">Upload Date and Time: </span>
            <span class="px-1">{{ formatToReadableDate(documentInfoRO.createDateTime) }}</span>
          </div>
          <div>
            <span class="font-bold">Documents Uploaded: </span>
            <span class="px-1">{{ documentInfoRO.filenames.length }}</span>
          </div>
          <div>
            <span class="font-bold">Documents: </span>
          </div>
          <div
            v-for="(filename, i) in documentInfoRO.filenames"
            :key="filename + i"
          >
            <span>{{ filename }}</span>
          </div>
        </div>

        <div class="flex flex-row gap-3 py-2 mt-12">
          <UButton
            block
            color="primary"
            class="h-[40px] w-[50%]"
            variant="outline"
            :loading="loadingDocuments"
            @click="navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })"
          >
            Back to Documents Services Page
          </UButton>

          <UButton
            block
            color="primary"
            class="h-[40px] w-[50%] font-bold"
            :loading="loadingDocuments"
            @click="requestDocumentRecord(documentInfoRO.consumerDocumentId)"
          >
            Download Document Record Statement
          </UButton>
        </div>

      </div>
    </div>
  </UModal>
</template>