<script setup lang="ts">
import { documentTypes } from '~/utils/documentTypes'
const { findCategoryByPrefix, getDocumentTypesByClass } = useDocuments()
const {
  searchDocumentId,
  searchEntityId,
  searchDocumentClass,
  searchDocumentType,
  searchDateRange
} = storeToRefs(useBcrosDocuments())

/** Watch the entity identifier and pre-populate document category when there is a prefix match **/
watch(() => searchEntityId.value, (id: string) => {
  // Format Entity Identifier
  searchEntityId.value = id.replace(/\s+/g, '')?.toUpperCase()
  // Assign and populate a prefix if a match is found
  if (id.length >= 1) findCategoryByPrefix(id, true)
})
/** Watch the document category and reset the document type on change **/
watch(() => searchDocumentClass.value, () => {
  searchDocumentType.value = ''
})
</script>
<template>
  <ContentWrapper name="document-search" class="mt-7 pb-10">
    <template #header>Document Search</template>
    <template #content>
      <span class="text-gray-700 font-normal text-base">
        Search for original registration documents and filings. Enter Entity ID or Document category to selected a
        date range to search by.
      </span>
      <div class="mt-8 grid grid-cols-2 gap-6">
        <div>
          <UFormGroup :help="'Enter the 8 digit document ID number'">
            <UInput
              v-model="searchDocumentId"
              class="mt-3"
              type="text"
              required
              placeholder="Document Id"
            />
          </UFormGroup>
        </div>

        <div>
          <UFormGroup :help="$t('documentIndexing.form.id.help')">
            <UInput
              v-model="searchEntityId"
              class="mt-3"
              type="text"
              required
              :placeholder="$t('documentIndexing.form.id.label')"
            />
          </UFormGroup>
        </div>

        <div class="col-span-2">
          <UFormGroup>
            <div class="grid grid-cols-4 gap-5 mt-3">
              <div class="col-span-2">
                <UFormGroup>
                  <USelectMenu
                    v-model="searchDocumentClass"
                    :placeholder="$t('documentIndexing.form.selectMenu.categoryLabel')"
                    select-class="text-gray-700"
                    :options="documentTypes"
                    value-attribute="class"
                    option-attribute="description"
                  />
                </UFormGroup>
              </div>

              <div class="col-span-2">
                <UFormGroup>
                  <USelectMenu
                    v-model="searchDocumentType"
                    :placeholder="$t('documentIndexing.form.selectMenu.typeLabel')"
                    select-class="text-gray-700"
                    :disabled="!searchDocumentClass"
                    :options="getDocumentTypesByClass(searchDocumentClass)"
                    value-attribute="type"
                    option-attribute="description"
                  />
                </UFormGroup>
              </div>
            </div>
          </UFormGroup>
        </div>

        <div>
          <UFormGroup help="Date range of registered documents you would like to search">
            <InputDatePicker
              v-model="searchDateRange"
              class="mt-3"
              is-ranged-picker
              :disabled="!searchDocumentType"
            />
          </UFormGroup>
        </div>
      </div>
    </template>
  </ContentWrapper>
</template>