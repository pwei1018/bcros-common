<script setup lang="ts">
const { searchDocuments, hasMinimumSearchCriteria } = useDocuments()
const { validateDocumentSearch } = storeToRefs(useBcrosDocuments())
</script>
<template>
  <div data-cy="document-management">
    <BcrosSection
      name="documentManagement"
      class="mt-12"
    >
      <template #header>
        <div class="grid grid-cols-6 gap-4 items-center">

          <div class="col-start-1 col-end-5">
            <h1 class="text-[32px] pb-2">{{ $t('title.documentManagement') }}</h1>
            <span class="text-gray-700 font-normal text-base">{{ $t('descriptions.documentManagement') }}</span>
          </div>

          <div class="col-end-7 col-span-2">
            <UButton
              class="py-2 px-6 text-base font-bold float-right"
              outlined
              color="primary"
              @click="navigateTo({ name: RouteNameE.DOCUMENT_INDEXING })"
            >
              {{ $t('button.documentIndexing') }}
              <UIcon
                name="i-mdi-chevron-right"
                class="bg-white text-xl"
              />
            </UButton>
          </div>
        </div>
      </template>
      <template #default>
        <DocumentSearch />
      </template>
    </BcrosSection>

    <div class="grid grid-cols-6 gap-4 mt-6">
      <div class="col-end-7 col-span-1">
        <UButton
          class="px-7 text-base font-bold h-[44px] float-right"
          outlined
          color="primary"
          @click="searchDocuments"
        >
          <UIcon
            name="i-mdi-search"
            class="bg-white text-xl"
          />
          Search
        </UButton>
      </div>
    </div>
    <span
      v-if="validateDocumentSearch && !hasMinimumSearchCriteria"
      class="text-red-500 float-right text-sm mt-3"
    >
      Enter or select search criteria
    </span>

    <!-- Document Search Results -->
    <DocumentsTable />
  </div>
</template>