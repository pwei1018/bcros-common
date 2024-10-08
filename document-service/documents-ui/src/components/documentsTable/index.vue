<script setup lang="ts">
import { formatToReadableDate } from "~/utils/dateHelper"
import { documentTypes, documentResultColumns } from "~/utils/documentTypes"
import { truncate } from "~/utils/documentRecords"
import type { DocumentInfoIF } from "~/interfaces/document-types-interface"
const {
  getDocumentDescription,
  getDocumentTypesByClass,
  findCategoryByPrefix
} = useDocuments()

const {
  searchDocumentRecords,
  getNextDocumentsPage,
  clearFilter,
} = useDocumentSearch() 

const {
  documentSearchResults,
  searchDocumentId,
  searchEntityId,
  searchDocument,
  searchDocumentType,
  searchDateRange,
  searchDescription,
  searchResultCount,
  searchDocumentClass,
  pageNumber,
  isLoading,
} = storeToRefs(useBcrosDocuments())

const documentRecordsTableRef = ref(null)
const columnsToShow = ref(documentResultColumns)
const isDescriptionExpanded = ref({})
const entityTypes = ref([])
const documentTypeOptions = ref(getDocumentTypesByClass())

const isFiltered = computed(() => {
  return (
    !!searchDocumentId.value ||
    !!searchEntityId.value ||
    !!searchDocument.value ||
    !!searchDocumentType.value ||
    !!searchDateRange.value?.start ||
    !!searchDateRange.value?.end
  )
})

const openDocumentRecord = (searchResult: DocumentInfoIF) => {
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
const toggleDescription = (consumerDocumentId) => {
  isDescriptionExpanded.value[consumerDocumentId] =
    !isDescriptionExpanded.value[consumerDocumentId]
}

const changeColumns = (selected: [string]) => {
  columnsToShow.value = documentResultColumns.filter(
    (column) => column.isFixed || selected.includes(column.key)
  )
}

onMounted(() => {
  searchDocumentRecords()
  const tableElement = documentRecordsTableRef.value?.$el
  if (tableElement) {
    tableElement.addEventListener("scroll", handleTableScroll)
  }
  // Insert empty options to document types for break lines on entity type.
  let currentRegistry = documentTypes[0].documents[0].productCode
  documentTypes.forEach((docType) => {
    // Insert empty option before new productCode(registry). 
    if (
      (currentRegistry !== docType.documents[0].productCode) 
      && (docType.documents[0].productCode !== 'nro')
    ) {
      entityTypes.value.push({
        class: 'BreakLine',
        description: '',
        disabled: true
      })
      currentRegistry = docType.documents[0].productCode
    }
    entityTypes.value.push(docType)
  })
})

onBeforeUnmount(() => {
  const tableElement = documentRecordsTableRef.value?.$el
  if (tableElement) {
    tableElement.removeEventListener("scroll", handleTableScroll)
  }
})

watch(() => [
    searchDocumentId.value,
    searchEntityId.value,
    searchDocument.value,
    searchDocumentType.value,
    searchDateRange.value,
  ], () => {
    pageNumber.value = 1
    searchDocumentRecords()
})

watch(() => searchEntityId.value, (id: string) => {
    // Format Entity Identifier
    searchEntityId.value = id.replace(/\s+/g, '')?.toUpperCase()
    // Assign and populate a prefix if a match is found
    if (id.length >= 1) findCategoryByPrefix(id, true)
})

watch(() => searchDocumentClass.value, (newValue: string) => {
  documentTypeOptions.value = getDocumentTypesByClass(newValue)
  if (!documentTypeOptions.value.some(docType => docType.type === searchDocumentType.value)) {
    searchDocumentType.value = ''
  }
})
</script>
<template>
  <ContentWrapper
    name="document-search-results"
    class="mt-8 mb-12"
    data-cy="document-search-results"
    :is-table="true"
  >
    <template #header>
      <div class="flex justify-between items-center">
        <span>
          {{ $t("documentSearch.table.title") }}
          ({{ searchResultCount || 0 }})
        </span>
        <div class="flex gap-4">
          <USelectMenu
            v-model="searchDocumentClass"
            :placeholder="$t('documentSearch.table.headers.entityType')"
            class="text-gray-700 font-light w-[300px]"
            :options="entityTypes"
            value-attribute="class"
            option-attribute="description"
            size="md"
            :ui="{
              icon: { trailing: { pointer: '' } },
              size: { md: 'h-[44px]' },
            }"
            :ui-menu="{ 
              height: 'max-h-65 h-[400px] w-full',
              option: {
                base: 'h-fit',
                padding: 'p-0',
                container: 'w-full h-fit'
              }
            }"
          >
            <template #option="{option}">
              <UDivider
                v-if="option.class === 'BreakLine'"
              />
              <span v-else class="truncate px-3 py-2 h-[44px] flex items-center">{{ option.description }}</span>
              
            </template>
            <template #trailing>
              <UButton
                v-show="searchDocumentClass !== ''"
                variant="link"
                icon="i-mdi-cancel-circle text-primary"
                :padded="false"
                @click="searchDocumentClass = ''"
              />
              <UIcon name="i-mdi-arrow-drop-down" class="w-5 h-5 text-gray-700  " />
            </template>
          </USelectMenu>
          <InputMultiSelector
            :options="documentResultColumns.filter((column) => !column.isFixed)"
            class="w-[250px] font-light"
            value-attribute="key"
            option-attribute="label"
            :label="$t('documentSearch.table.headers.columnsToShow')"
            @change-columns="changeColumns"
          />
        </div>
      </div>
    </template>
    <template #content>
      <UTable
        ref="documentRecordsTableRef"
        :columns="columnsToShow"
        :rows="documentSearchResults || []"
        :loading="isLoading"
        :empty-state="{
          icon: null,
          label: $t('documentSearch.table.noResult'),
        }"
      >
        <template #emptyColumn-header="{ column }">
          <div
            class="uppercase font-normal text-xs text-bcGovGray-700 font-sans"
          >
            <div class="flex align-center pl-5 pb-1">
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
        <template #consumerFilenames-header="{ column }">
          <DocumentsTableInputHeader
            v-model="searchDocument"
            :column="column"
          />
        </template>
        <template #documentTypeDescription-header="{ column }">
          <div class="px-2">
            <DocumentsTableSortButton :label="column.label" />
          </div>
          <UDivider class="my-3" />
          <div>
            <div class="h-11">
              <USelectMenu
                v-model="searchDocumentType"
                :placeholder="column.label"
                class="w-full px-2 font-light w-[250px]"
                select-class="text-gray-700"
                :options="documentTypeOptions"
                value-attribute="type"
                option-attribute="description"
                size="md"
                :ui="{
                  icon: { trailing: { pointer: '' } },
                  size: { md: 'h-[44px]' },
                }"
              >
                <template #trailing>
                  <UButton
                    v-show="searchDocumentType !== ''"
                    variant="link"
                    icon="i-mdi-cancel-circle text-primary"
                    :padded="false"
                    @click="searchDocumentType = ''"
                  />
                  <UIcon name="i-mdi-arrow-drop-down" class="w-5 h-5 " />
                </template>
              </USelectMenu>
            </div>
          </div>
        </template>
        <template #consumerFilingDateTime-header="{ column }">
          <div class="px-2">
            <DocumentsTableSortButton :label="column.label" />
          </div>
          <UDivider class="my-3" />
          <div>
            <div class="h-11">
              <InputDatePicker
                v-model="searchDateRange"
                class="w-[265px] px-2 font-light"
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
            v-model="searchDescription"
            :column="column"
          />
        </template>
        <template #actions-header="{ column }">
          <!-- eslint-disable-next-line -->
          <div class="flex justify-center align-center flex-col h-full border-l-4 border-solid border-gray-200 bg-white min-h-[120px]">
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
                  @click="clearFilter"
                />
              </div>
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
        <template #consumerFilenames-data="{ row }">
          <div v-if="row.consumerFilenames.length > 1">
            <span
              v-for="(file, i) in row.consumerFilenames"
              :key="`file-${i}`"
              class="block my-2"
            >
              <DocumentsTableDownloadLink
                :download-url="row.consumerFilenames[i]"
                :file-name="file"
              />
            </span>
            <span class="my-2">
              <ULink inactive-class="text-primary" class="flex align-center">
                <UIcon name="i-mdi-download" class="w-5 h-5 mr-1.5" />
                {{ $t("documentSearch.table.downloadAll") }}
              </ULink>
            </span>
          </div>
          <div v-else>
            <span class="block my-2">
              <DocumentsTableDownloadLink
                :download-url="row.consumerFilenames[0]"
                :file-name="row.consumerFilenames[0]"
              />
            </span>
          </div>
        </template>
        <template #description-data="{ row }">
          <div v-if="row.description" class="w-[300px]">
            <p>
              {{
                isDescriptionExpanded[row.consumerDocumentId]
                  ? row.description
                  : truncate(row.description, 150, 145)
              }}
            </p>
            <ULink
              v-if="row.description.length > 150"
              class="text-primary"
              @click="toggleDescription(row.consumerDocumentId)"
            >
              {{
                isDescriptionExpanded[row.consumerDocumentId]
                  ? "Read Less"
                  : "Read More"
              }}
            </ULink>
          </div>
        </template>
        <!-- Actions -->
        <template #actions-data="{ row }">
          <div
            class="flex justify-center items-center h-full border-l-4 border-solid border-gray-200 bg-white"
          >
            <UButton
              class="relative h-[35px] px-8 text-base"
              outlined
              color="primary"
              @click="openDocumentRecord(row)"
            >
              {{ $t("button.open") }}
            </UButton>
          </div>
        </template>
      </UTable>
    </template>
  </ContentWrapper>
</template>
