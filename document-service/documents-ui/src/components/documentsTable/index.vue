<script setup lang="ts">
import { formatToReadableDate } from "~/utils/dateHelper"
import { documentResultColumns } from "~/utils/documentTypes"
import type { DocumentInfoIF } from "~/interfaces/document-types-interface"
const {
  getDocumentDescription,
  downloadFileFromUrl,
  searchDocumentRecords,
  getDocumentTypesByClass,
  getNextDocumentsPage,
} = useDocuments()

const {
  documentList,
  documentRecord,
  documentSearchResults,
  searchDocumentId,
  searchEntityId,
  searchDocuments,
  searchDocumentType,
  searchDateRange,
  isLoading,
} = storeToRefs(useBcrosDocuments())

const documentRecordsTableRef = ref(null)
const documentRecordColumns = ref([])

const isFiltered = computed(() => {
  return (
    !!searchDocumentId.value ||
    !!searchEntityId.value ||
    !!searchDocuments.value ||
    !!searchDocumentType.value ||
    !!searchDateRange.value
  )
})

const openDocumentRecord = (searchResult: DocumentInfoIF) => {
  documentRecord.value = { ...searchResult }
  documentList.value = searchResult.consumerFilenames?.map((file) => ({
    name: file,
  }))
  navigateTo({
    name: RouteNameE.DOCUMENT_RECORDS,
    params: { identifier: searchResult.consumerDocumentId },
  })
}

const handleTableScroll = () => {
  if (documentRecordsTableRef.value) {
    const scrollTop = documentRecordsTableRef.value.$el.scrollTop
    const scrollHeight = documentRecordsTableRef.value.$el.scrollHeight
    const clientHeight = documentRecordsTableRef.value.$el.clientHeight
    if (scrollTop + clientHeight >= scrollHeight) {
      getNextDocumentsPage()
    }
  }
}

onMounted(() => {
  documentRecordColumns.value = documentResultColumns()
  searchDocumentRecords()

  const tableElement = documentRecordsTableRef.value?.$el
  if (tableElement) {
    tableElement.addEventListener("scroll", handleTableScroll)
  }
})

onBeforeUnmount(() => {
  const tableElement = documentRecordsTableRef.value?.$el
  if (tableElement) {
    tableElement.removeEventListener("scroll", handleTableScroll)
  }
})
</script>
<template>
  <ContentWrapper
    name="document-search-results"
    class="my-12"
    data-cy="document-search-results"
    :is-table="true"
  >
    <template #header>
      <div class="flex justify-between items-center">
        <span>{{ $t("documentSearch.table.title") }} (123)</span>
      </div>
    </template>
    <template #content>
      <UTable
        ref="documentRecordsTableRef"
        :columns="documentRecordColumns"
        :rows="documentSearchResults || []"
        :sort-button="{
          class: 'font-bold text-sm',
          size: '2xs',
          square: false,
          ui: { rounded: 'rounded-full' },
        }"
        :loading="isLoading"
        :empty-state="{
          icon: null,
          label: $t('documentSearch.table.noResult'),
        }"
      >
        <template #emptyColumn-header="{ column }">
          <div
            class="uppercase font-normal text-sm text-bcGovGray-700 font-sans"
          >
            <div class="flex align-center pl-5">
              {{ column.label }}
            </div>
            <UDivider class="my-3 w-full" />
            <div class="flex align-center items-center pl-5 h-11">
              {{ $t("documentSearch.table.headers.filterBy") }}
            </div>
          </div>
        </template>
        <template #consumerDocumentId-header="{ column }">
          <DocumentsTableInputHeader
            v-model="searchDocumentId"
            :column="column"
          />
        </template>
        <template #consumerIdentifier-header="{ column }">
          <DocumentsTableInputHeader
            v-model="searchEntityId"
            :column="column"
          />
        </template>
        <template #documentURL-header="{ column }">
          <DocumentsTableInputHeader
            v-model="searchDocuments"
            :column="column"
          />
        </template>
        <template #documentTypeDescription-header="{ column }">
          <div class="px-2">
            {{ column.label }}
          </div>
          <UDivider class="my-3" />
          <div>
            <div class="h-11">
              <USelectMenu
                v-model="searchDocumentType"
                :placeholder="column.label"
                class="w-full px-2 font-light"
                select-class="text-gray-700"
                :options="getDocumentTypesByClass()"
                value-attribute="type"
                option-attribute="description"
                size="md"
                :popper="{ placement: 'bottom-start' }"
                :ui="{
                  icon: { trailing: { pointer: '' } },
                  size: { md: 'h-[44px]' },
                }"
              >
                <template #trailing>
                  <UButton
                    v-show="searchDocumentType !== ''"
                    color="gray"
                    variant="link"
                    icon="i-mdi-cancel-circle text-primary"
                    :padded="false"
                    @click="searchDocumentType = ''"
                  />
                </template>
              </USelectMenu>
            </div>
          </div>
        </template>
        <template #consumerFilingDateTime-header="{ column }">
          <div class="px-2">
            {{ column.label }}
          </div>
          <UDivider class="my-3" />
          <div>
            <div class="h-11">
              <InputDatePicker
                v-model="searchDateRange"
                class="w-full px-2 font-light"
                is-ranged-picker
                is-left-bar
                is-filter
                size="md"
              />
            </div>
          </div>
        </template>
        <template #description-header="{ column }">
          <DocumentsTableInputHeader
            v-model="searchDocumentId"
            :column="column"
          />
        </template>
        <template #actions-header="{ column }">
          <div class="px-2">
            {{ column.label }}
          </div>
          <UDivider class="my-3" />
          <div>
            <div class="flex justify-center h-11">
              <UButton
                v-if="isFiltered"
                class="h-[44px] px-3 py-3 text-sm"
                :label="$t('documentSearch.table.clearFilter')"
                icon="i-mdi-cancel-circle"
                variant="outline"
                color="primary"
              />
            </div>
          </div>
        </template>

        <!-- Entity ID -->
        <template #consumerIdentifier-data="{ row }">
          <div>
            {{ row.consumerIdentifier }}
          </div>
          <div class="italic text-xs text-bcGovGray-700">
            {{ getDocumentTypesByClass(row.documentClass)[0].description }}
          </div>
        </template>
        <!-- Document class -->
        <template #documentClass-data="{ row }">
          {{ getDocumentDescription(row.documentClass) }}
        </template>

        <!-- Consumer DateTime -->
        <template #consumerFilingDateTime-data="{ row }">
          {{ formatToReadableDate(row.consumerFilingDateTime, true) }}
        </template>

        <!-- Document URL -->
        <template #documentURL-data="{ row }">
          <div v-if="row.consumerFilenames.length > 1">
            <span
              v-for="(file, i) in row.consumerFilenames"
              :key="`file-${i}`"
              class="block my-1"
            >
              <ULink
                inactive-class="text-primary"
                class="flex align-center"
                @click="downloadFileFromUrl(row.documentUrls[i], file)"
              >
                <UIcon name="i-mdi-file-download" class="w-5 h-5" />
                {{ file }}
              </ULink>
            </span>
            <span>
              <ULink inactive-class="text-primary" class="flex align-center">
                <UIcon name="i-mdi-download" class="w-5 h-5" />
                {{ $t("documentSearch.table.downloadAll") }}
              </ULink>
            </span>
          </div>
          <div v-else>
            <span class="block my-1">
              <ULink
                inactive-class="text-primary"
                class="flex align-center"
                @click="
                  downloadFileFromUrl(
                    row.documentUrls[0],
                    row.consumerFilenames[0]
                  )
                "
              >
                <UIcon name="i-mdi-file-download" class="w-5 h-5" />
                {{ row.consumerFilenames[0] }}
              </ULink>
            </span>
          </div>
        </template>
        <!-- Actions -->
        <template #actions-data="{ row }">
          <UButton
            class="relative h-[35px] px-8 text-base"
            outlined
            color="primary"
            @click="openDocumentRecord(row)"
          >
            {{ $t("button.open") }}
          </UButton>
        </template>
      </UTable>
    </template>
  </ContentWrapper>
</template>
