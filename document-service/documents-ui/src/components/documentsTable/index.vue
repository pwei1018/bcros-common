<script setup lang="ts">
import { formatToReadableDate } from '~/utils/dateHelper'
import { documentResultColumns } from '~/utils/documentTypes'
import type { DocumentInfoIF } from '~/interfaces/document-types-interface'
const { getDocumentDescription, downloadFileFromUrl } = useDocuments()
const { documentList, documentRecord, documentSearchResults, searchEntityId } = storeToRefs(useBcrosDocuments())

const openDocumentRecord = (searchResult: DocumentInfoIF) => {
  documentRecord.value = { ...searchResult, }
  documentList.value = searchResult.consumerFilenames?.map(file => ({ name: file }))
  navigateTo({ name: RouteNameE.DOCUMENT_RECORDS, params: { identifier: searchResult.consumerDocumentId } })
}
</script>
<template>
  <ContentWrapper
    v-if="documentSearchResults && !!documentSearchResults.length"
    name="document-search-results"
    class="my-12"
    data-cy="document-search-results"
  >
    <template #header>
      <div class="flex justify-between items-center">
        <span>Search Results</span>
      </div>
    </template>
    <template #content>

      <div class="flex flex-row pl-4 text-gray-700">
        <span class="font-bold">Results: </span><span class="pl-2">({{ documentSearchResults.length }})</span>
        <span class="px-4">|</span>
        <span class="font-bold">Entity ID: </span><span class="pl-2">{{ searchEntityId}}</span>
      </div>

      <UTable
        class="mt-8"
        :columns="documentResultColumns"
        :rows="documentSearchResults || []"
        :sort-button="{
          class: 'font-bold text-sm',
          size: '2xs',
          square: false,
          ui: { rounded: 'rounded-full' }
        }"
      >

        <!-- Document URL -->
        <template #documentClass-data="{ row }">
          {{ getDocumentDescription(row.documentClass) }}
        </template>

        <!-- Consumer DateTime -->
        <template #consumerFilingDateTime-data="{ row }">
          {{ formatToReadableDate(row.consumerFilingDateTime, true) }}
        </template>

        <!-- Document URL -->
        <template #documentURL-data="{ row }">
          <span
            v-for="(file, i) in row.consumerFilenames"
            :key="`file-${i}`"
          >
             <ULink
               inactive-class="text-primary underline"
               @click="downloadFileFromUrl(row.documentUrls[i], file)"
             >
              {{ file }}
            </ULink>
          </span>
        </template>

        <!-- Actions -->
        <template #actions-data="{ row }">
          <UButton
            class="h-[35px] px-8 text-base"
            outlined
            color="primary"
            @click="openDocumentRecord(row)"
          >
            {{ $t('button.open') }}
          </UButton>
        </template>
      </UTable>
    </template>
  </Contentwrapper>
</template>
