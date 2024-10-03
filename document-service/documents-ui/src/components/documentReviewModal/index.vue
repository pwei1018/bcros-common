<script setup lang="ts">
import { formatToReadableDate } from '~/utils/dateHelper'
import { getDocumentRecordReport } from '~/utils/documentRequests'
const { getDocumentDescription } = useDocuments()
const { displayDocumentReview, documentInfoRO } = storeToRefs(useBcrosDocuments())
const loadingDocuments = ref(false)

/**
 * Fetch and download the document record.
 * Navigates to the Document Manage Page.
 *
 * @param consumerId - The consumer ID to fetch the document record for.
 */
const requestDocumentRecord = async (consumerId: string) => {
  loadingDocuments.value = true
  await getDocumentRecordReport(consumerId)
  loadingDocuments.value = false
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
          <h3 class="text-[24px] font-bold">{{ $t('documentReview.title') }}</h3>
        </div>

        <div class="flex flex-row py-6">
          <span class="text-gray-700 font-normal text-base leading-6">{{ $t('documentReview.description') }}</span>
        </div>

        <div class="grid grid-flow-row auto-rows-max">
          <div>
            <span class="font-bold">{{ $t('documentReview.labels.documentId') }}: </span>
            <span class="px-1">{{ documentInfoRO.consumerDocumentId }}</span>
          </div>
          <div>
            <span class="font-bold">{{ $t('documentReview.labels.entityId') }}: </span>
            <span class="px-1">{{ documentInfoRO.consumerIdentifier || 'Not Entered' }}</span>
          </div>
          <div>
            <span class="font-bold">{{ $t('documentReview.labels.documentCategory') }}: </span>
            <span class="px-1">{{ getDocumentDescription(documentInfoRO.documentClass) }}</span>
          </div>
          <div>
            <span class="font-bold">{{ $t('documentReview.labels.documentType') }}: </span>
            <span class="px-1">{{ getDocumentDescription(documentInfoRO.documentType, true) }}</span>
          </div>
          <div>
            <span class="font-bold">{{ $t('documentReview.labels.filingDate') }}: </span>
            <span class="px-1">{{ formatToReadableDate(documentInfoRO.consumerFilingDateTime) || 'Not Entered' }}</span>
          </div>

          <div class="pt-8">
            <span class="font-bold">{{ $t('documentReview.labels.uploadDate') }}: </span>
            <span class="px-1">{{ formatToReadableDate(documentInfoRO.createDateTime) }}</span>
          </div>
          <div>
            <span class="font-bold">{{ $t('documentReview.labels.documentsUploaded') }}: </span>
            <span class="px-1">{{ documentInfoRO.filenames.length }}</span>
          </div>
          <div>
            <span class="font-bold">{{ $t('documentReview.labels.documentListLabel') }}: </span>
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
            {{ $t('documentReview.buttonLabels.cancel') }}
          </UButton>

          <UButton
            block
            color="primary"
            class="h-[40px] w-[50%] font-bold"
            :loading="loadingDocuments"
            @click="requestDocumentRecord(documentInfoRO.consumerDocumentId)"
          >
            {{ $t('documentReview.buttonLabels.downloadReport') }}
          </UButton>
        </div>

      </div>
    </div>
  </UModal>
</template>