<script setup lang="ts">
import { formatToReadableDate } from '~/utils/dateHelper'
import { getScanningRecord } from '~/utils/documentRequests'

const emit = defineEmits(['openEdit'])
const { documentRecord } = storeToRefs(useBcrosDocuments())
const { downloadFileFromUrl, getDocumentDescription } = useDocuments()
const identifier = useRoute()?.params?.identifier as string

onMounted(async () => {
  if (!documentRecord.value) {
    // TODO: Fetch Record if absent (ie coming from another app with identifier) Requires isolated DocumentID Endpoint
    await navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
  }

  if(!documentRecord.value?.accessionNumber) {
    try {
      const scanningData = await getScanningRecord(documentRecord.value.documentClass, identifier)
      documentRecord.value = { ...documentRecord.value, ...scanningData }
    } catch (error) {
      console.error('Error fetching document scanning record', error)
    }
  }
})
</script>
<template>
  <ContentWrapper
    v-if="!!documentRecord"
    name="document-record"
    class="mt-7 pb-10"
    data-cy="document-record"
  >
    <template #header>
      <div class="flex justify-between">
        <div>{{ $t('documentRecord.subtitle') }}</div>
        <div>
          <UButton
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
      <div class="grid grid-cols-3 auto-rows-max">

        <!-- Document Meta Data -->
        <span class="font-bold">{{ $t('documentReview.labels.entityId') }} </span>
        <span class="col-span-2">{{ documentRecord.consumerIdentifier || 'Not Entered' }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.documentId') }} </span>
        <span class="col-span-2">{{ documentRecord.consumerDocumentId }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.documentCategory') }} </span>
        <span class="col-span-2">{{ getDocumentDescription(documentRecord.documentClass) }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.documentType') }} </span>
        <span class="col-span-2">{{ getDocumentDescription(documentRecord.documentType, true) }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.filingDate') }} </span>
        <span class="col-span-2">
          {{ formatToReadableDate(documentRecord.consumerFilingDateTime) || 'Not Entered' }}
        </span>

        <span class="font-bold">{{ $t('documentReview.labels.uploadDate') }} </span>
        <span class="col-span-2">{{ formatToReadableDate(documentRecord.createDateTime) }}</span>

        <!-- Scanning Information -->
        <UDivider class="my-6 col-span-3" />
        <span class="font-bold">{{ $t('documentReview.labels.scanningLabel') }} </span>
        <span class="col-span-2"/>

        <span class="font-bold">{{ $t('documentReview.labels.accessionNumber') }} </span>
        <span class="col-span-2">{{ documentRecord.accessionNumber }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.batchId') }} </span>
        <span class="col-span-2">{{ documentRecord.batchId }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.pagesToScan') }} </span>
        <span class="col-span-2">{{ documentRecord.pageCount }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.scannedDate') }} </span>
        <span class="col-span-2">{{ documentRecord.scanDateTime }}</span>

        <span class="font-bold">{{ $t('documentReview.labels.author') }} </span>
        <span class="col-span-2">{{ documentRecord.author }}</span>

        <!-- Document Files -->
        <UDivider class="my-6 col-span-3" />

        <span class="font-bold">{{ $t('documentReview.labels.documentListLabel') }}</span>
        <span class="col-span-2 flex flex-col">
          <span
            v-for="(file, i) in documentRecord.consumerFilenames"
            :key="`file-${i}`"
            class="spanLink pb-2"
          >
             <ULink
               inactive-class="text-primary underline"
               @click="downloadFileFromUrl(documentRecord.documentUrls[i], file)"
             >
               {{ file }}
             </ULink>
          </span>
        </span>
      </div>
    </template>
  </ContentWrapper>
</template>
<style scoped lang="scss">
span:not(.spanLink) {
  padding: 0.5rem 0;
}
</style>