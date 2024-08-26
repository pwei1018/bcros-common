<script setup lang="ts">
import { formatToReadableDate } from '~/utils/dateHelper'
const { getDocumentClassDescription, downloadFileFromUrl } = useDocuments()
const { documentSearchResults } = storeToRefs(useBcrosDocuments())
const { searchEntityId } = storeToRefs(useBcrosDocuments())
const documentResultCols = [
  {
    key: 'consumerIdentifier',
    label: 'Entity ID',
    sortable: true
  },
  {
    key: 'consumerDocumentId',
    label: 'Document ID',
    sortable: true
  },
  {
    key: 'documentClass',
    label: 'Document Category'
  },
  {
    key: 'documentTypeDescription',
    label: 'Document Type'
  },
  {
    key: 'consumerFilingDateTime',
    label: 'Filing Date'
  },
  {
    key: 'documentURL',
    label: 'Documents'
  },
  {
    key: 'actions',
    label: 'Actions'
  }
]
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
        <!-- Column Selection Pending User Preferences -->
<!--        <UFormGroup>-->
<!--          <USelectMenu-->
<!--            v-model="selectedColumns"-->
<!--            multiple-->
<!--            placeholder="Columns to Show"-->
<!--            select-class="text-gray-700"-->
<!--            :options="documentResultCols"-->
<!--            value-attribute="key"-->
<!--            option-attribute="label"-->
<!--          />-->
<!--        </UFormGroup>-->
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
        :columns="documentResultCols"
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
          {{ getDocumentClassDescription(row.documentClass) }}
        </template>

        <!-- Consumer DateTime -->
        <template #consumerFilingDateTime-data="{ row }">
          {{ formatToReadableDate(row.consumerFilingDateTime, true) }}
        </template>

        <!-- Document URL -->
        <template #documentURL-data="{ row }">
            <ULink
              v-for="(file, i) in row.consumerFilenames"
              :key="`file-${i}`"
              inactive-class="text-primary underline"
              @click="downloadFileFromUrl(row.documentUrls[i], file)"
            >
              {{ file }}
            </ULink>
          <br>
        </template>

        <!-- Actions -->
        <template #actions-data="{ row }">
          <UButton
            class="h-[35px] px-8 text-base"
            outlined
            color="primary"
            @click="navigateTo({ name: RouteNameE.DOCUMENT_RECORDS, params: { documentId: row.consumerDocumentId } })"
          >
            {{ $t('button.open') }}
          </UButton>
        </template>
      </UTable>
    </template>
  </Contentwrapper>
</template>
