<script setup lang="ts">
import { formatToReadableDate } from '~/utils/dateHelper'
const { getDocumentClassDescription, downloadFileFromUrl } = useDocuments()
const { documentSearchResults } = storeToRefs(useBcrosDocuments())
const documentResultCols = [
  {
    key: 'consumerIdentifier',
    label: 'Entity ID'
  },
  {
    key: 'consumerDocumentId',
    label: 'Document ID'
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
    <template #header>Search Results ({{ documentSearchResults.length }})</template>
    <template #content>
      <UTable
        :columns="documentResultCols"
        :rows="documentSearchResults || []"
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
      </UTable>
    </template>
  </Contentwrapper>
</template>
