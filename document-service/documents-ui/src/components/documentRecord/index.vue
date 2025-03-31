<script setup lang="ts">
import { formatToReadableDate } from '~/utils/dateHelper'
const emit = defineEmits(['openEdit'])
defineProps({
  isReviewMode: {
    type: Boolean,
    default: false
  }
})
const {
  uploadedDocumentList,
  documentRecord,
  documentRecordSnapshot,
  scanningDetails,
  scanningDetailsSnapshot
} = storeToRefs(useBcrosDocuments())
const { updatedDocumentList, fetchUrlAndDownload, getDocumentDescription } = useDocuments()
const isScanPending = computed(() => documentRecord.value.consumerDocumentId.length === 8 &&
  !scanningDetails.value?.scanDateTime)
</script>
<template>
  <ContentWrapper
    v-if="!!documentRecord"
    name="document-record"
    class="pb-10"
    data-cy="document-record"
  >
    <template #header>
      <div class="flex justify-between">
        <div class="flex">
          <UIcon name="i-mdi-text-box" class="w-6 h-6 text-blue-350" />
          <div class="ml-2">{{ $t('documentRecord.subtitle') }}</div>
        </div>
        <div v-if="!isReviewMode">
          <UButton
            class="hover:bg-transparent"
            variant="ghost"
            icon="i-mdi-pencil"
            :label="$t('documentRecord.editButton')"
            data-cy="edit-record-button"
            @click="emit('openEdit')"
          />
        </div>
      </div>
    </template>
    <template #content>
      <div :class="['grid grid-cols-3 auto-rows-max', updatedDocumentList.length ? 'pb-6' : 'pb-8']">
        <!-- Document Meta Data -->
        <span class="font-bold">{{ $t('documentReview.labels.documentId') }}</span>
        <span class="col-span-2">{{ documentRecord.consumerDocumentId }}</span>

        <span class="font-bold grid">
          {{ $t('documentReview.labels.entityId') }}
          <HasChangesBadge
            v-if="isReviewMode"
            class="w-[65px]"
            :baseline="documentRecordSnapshot.consumerIdentifier"
            :current-state="documentRecord.consumerIdentifier"
          />
        </span>
        <span class="col-span-2">{{ documentRecord.consumerIdentifier || 'Not Entered' }}</span>

        <span class="font-bold grid">
          {{ $t('documentReview.labels.documentCategory') }}
          <HasChangesBadge
            v-if="isReviewMode"
            class="w-[65px]"
            :baseline="documentRecordSnapshot.documentClass"
            :current-state="documentRecord.documentClass"
          />
        </span>
        <span class="col-span-2">{{ getDocumentDescription(documentRecord.documentClass) }}</span>

        <span class="font-bold grid">
          {{ $t('documentReview.labels.documentType') }}
          <HasChangesBadge
            v-if="isReviewMode"
            class="w-[65px]"
            :baseline="documentRecordSnapshot.documentType"
            :current-state="documentRecord.documentType"
          />
        </span>
        <span class="col-span-2">{{ getDocumentDescription(documentRecord.documentType, true) }}</span>

        <span class="font-bold grid">
          {{ $t('documentReview.labels.description') }}
          <HasChangesBadge
            v-if="isReviewMode"
            class="w-[65px]"
            :baseline="documentRecordSnapshot.description"
            :current-state="documentRecord.description"
          />
        </span>
        <span class="col-span-2">{{ documentRecord.description }}</span>

        <span class="font-bold grid">
          {{ $t('documentReview.labels.filingDate') }}
          <HasChangesBadge
            v-if="isReviewMode"
            class="w-[65px]"
            :baseline="documentRecordSnapshot.consumerFilingDateTime"
            :current-state="documentRecord.consumerFilingDateTime"
          />
        </span>
        <span class="col-span-2">
          {{ formatToReadableDate(documentRecord.consumerFilingDateTime, true) || 'Not Entered' }}
        </span>
        <span class="font-bold">{{ $t('documentReview.labels.author') }}</span>
        <span class="col-span-2">{{ documentRecord?.author }}</span>

        <!-- Scanning Information -->
        <UDivider class="my-6 col-span-3" />
        <span class="font-bold grid">
          {{ $t('documentReview.labels.scanningLabel') }}
          <HasChangesBadge
            v-if="isReviewMode"
            class="w-[65px]"
            :baseline="scanningDetailsSnapshot"
            :current-state="scanningDetails"
          />
        </span>
        <span class="col-span-2">
          <UBadge
            v-if="isScanPending"
            variant="solid"
            color="primary"
            label="SCAN PENDING"
            class="badge px-2.5 py-1.5"
          />
        </span>

        <span class="font-bold">{{ $t('documentReview.labels.accessionNumber') }}</span>
        <span class="col-span-2">{{ scanningDetails?.accessionNumber }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.batchId') }}</span>
        <span class="col-span-2">{{ scanningDetails?.batchId }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.pagesToScan') }}</span>
        <span class="col-span-2">{{ scanningDetails?.pageCount }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.scannedDate') }}</span>
        <span class="col-span-2">
          {{ scanningDetails?.scanDateTime ? formatToReadableDate(scanningDetails?.scanDateTime, true) : '' }}
        </span>

        <!-- Document Files -->
        <UDivider class="my-6 col-span-3" />

        <span class="font-bold grid">
          {{ $t('documentReview.labels.documentListLabel') }}
          <HasChangesBadge
            v-if="isReviewMode"
            class="w-[65px]"
            :baseline="[]"
            :current-state="uploadedDocumentList"
          />
        </span>
        <span class="col-span-2 flex flex-col">
          <span
            v-for="(file, i) in updatedDocumentList"
            :key="`file-${i}`"
            class="spanLink pb-2"
          >
             <ULink
               inactive-class="text-primary underline"
               :disabled="isReviewMode"
               @click="fetchUrlAndDownload(
                  documentRecordSnapshot.documentClass,
                  documentRecordSnapshot.documentServiceIds[i]
                )"
              >
               {{ file.name }}
             </ULink>
          </span>
        </span>
      </div>
    </template>
  </ContentWrapper>
</template>
<style scoped lang="scss">
span:not(.spanLink, .badge, #updated-badge-component) {
  padding: 0.5rem 0;
}
</style>
