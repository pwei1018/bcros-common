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
    <template #header>{{ $t('documentSearch.title') }}</template>
    <template #content>
      <span class="text-gray-700 font-normal text-base">
        {{ $t('documentSearch.description') }}
      </span>
      <div class="mt-8 grid grid-cols-2 gap-6">
        <div>
          <UFormGroup :help="$t('documentSearch.form.docId.help')">
            <UInput
              v-model="searchDocumentId"
              class="mt-3"
              type="text"
              required
              :placeholder="$t('documentSearch.form.docId.label')"
            />
          </UFormGroup>
        </div>

        <div>
          <UFormGroup :help="$t('documentSearch.form.id.help')">
            <UInput
              v-model="searchEntityId"
              class="mt-3"
              type="text"
              required
              :placeholder="$t('documentSearch.form.id.label')"
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
                    :placeholder="$t('documentSearch.form.selectMenu.categoryLabel')"
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
                    :placeholder="$t('documentSearch.form.selectMenu.typeLabel')"
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
          <UFormGroup :help="$t('documentSearch.form.dateRange.help')">
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