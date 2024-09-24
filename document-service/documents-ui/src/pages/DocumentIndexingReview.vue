<script setup lang="ts">
import { formatToReadableDate } from '~/utils/dateHelper'
import { useBcrosDocuments } from '~/stores/documents'

const { getDocumentDescription } = useDocuments()
const {
  consumerDocumentId,
  consumerIdentifier,
  description,
  documentClass,
  documentType,
  documentList,
  consumerFilingDate
} = storeToRefs(useBcrosDocuments())
</script>
<template>
  <div
    class="grid grid-cols-8 gap-4 mt-12 mb-16"
    :data-cy="'document-indexing-review'"
  >

    <div class="col-span-6">
      <BcrosSection name="documentIndexingReview">
        <template #header>
          <div class="grid grid-cols-6">
            <div class="col-span-6">
              <h1 class="text-[32px] pb-2">{{ $t('documentIndexing.reviewLabel') }}</h1>
              <span class="text-gray-700 font-normal text-base">{{ $t('documentIndexing.reviewSubtitle') }}</span>
            </div>
          </div>
        </template>

        <template #default>
          <ContentWrapper
            name="document-record"
            class="mt-6 pb-10"
            data-cy="document-record"
          >
            <template #header>
              <div class="flex">
                <UIcon name="i-mdi-text-box" class="w-6 h-6 text-blue-350" />
                <span class="ml-2">{{ $t('documentRecord.subtitle') }}</span>
              </div>
            </template>
            <template #content>
              <div class="pr-4">
                <div class="grid grid-flow-row auto-rows-max">
                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentIndexing.label') }}</span>
                  </div>
                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentReview.labels.documentId') }}</span>
                    <span class="px-1 col-span-2">
                      {{ consumerDocumentId || 'Will be automatically generated when the document record is saved' }}
                    </span>
                  </div>
                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentReview.labels.entityId') }}</span>
                    <span class="px-1 col-span-2">{{ consumerIdentifier || 'Not Entered' }}</span>
                  </div>
                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentReview.labels.documentCategory') }}</span>
                    <span class="px-1 col-span-2">{{ getDocumentDescription(documentClass) }}</span>
                  </div>
                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentReview.labels.documentType') }}</span>
                    <span class="px-1 col-span-2">{{ getDocumentDescription(documentType, true) }}</span>
                  </div>
                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentReview.labels.description') }}</span>
                    <span class="px-1 col-span-2">{{ description }}</span>
                  </div>
                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentReview.labels.filingDate') }}</span>
                    <span class="px-1 col-span-2">
                      {{ formatToReadableDate(consumerFilingDate, true) || 'Not Entered' }}
                    </span>
                  </div>

                  <UDivider class="my-7" />

                  <div class="py-1 grid grid-cols-3">
                    <span class="font-bold text-gray-900">{{ $t('documentReview.labels.documentListLabel') }}</span>
                    <div class="col-span-2">
                      <ol
                        v-for="(document, i) in documentList"
                        :key="document + i"
                        class="py-2"
                      >
                        {{ document.name }}
                      </ol>
                    </div>
                  </div>
              </div>
            </div></template>
          </ContentWrapper>
        </template>
      </BcrosSection>
    </div>
  </div>
</template>