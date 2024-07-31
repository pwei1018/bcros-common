<template>
  <FormWrapper
    id="document-indexing-form"
    name="document-indexing-form"
    class="rounded"
    data-cy="document-indexing-form"
  >
    <template #label>
      <h2 class="text-[16px] leading-6 font-bold">{{ $t('documentIndexing.label') }}</h2>
    </template>

    <template #form>
      <div class="grid grid-flow-row auto-rows-max">
        <UFormGroup
          :label="$t('documentIndexing.form.id.label')"
          :description="$t('documentIndexing.form.id.description')"
          :help="$t('documentIndexing.form.id.help')"
        >
          <UInput
            v-model="entityId"
            class="mt-3 text-gray-200"
            content="text-gray-700"
            :placeholder="$t('documentIndexing.form.id.label')"
            type="text"
            required
            :disabled="noIdCheckbox"
          />
        </UFormGroup>

        <UCheckbox
          v-model="noIdCheckbox"
          class="mt-5"
          name="unknown-id-checkbox"
          :label="$t('documentIndexing.form.checkbox.label')"
        />

        <UDivider class="my-7" />

        <UFormGroup :label="$t('documentIndexing.form.selectMenu.label')">
          <div class="grid grid-cols-4 gap-5 mt-3">
            <div class="col-span-2">
              <USelectMenu
                v-model="documentCategory"
                :placeholder="$t('documentIndexing.form.selectMenu.categoryLabel')"
                select-class="text-gray-700"
                :options="getCategories()"
              />
            </div>

            <div class="col-span-2">
              <USelectMenu
                v-model="documentType"
                :placeholder="$t('documentIndexing.form.selectMenu.typeLabel')"
                select-class="text-gray-700"
                :disabled="!documentCategory"
                :options="getDocumentsByCategory(documentCategory)"
              />
            </div>
          </div>
        </UFormGroup>

        <UDivider class="my-7" />

        <UFormGroup
          :label="$t('documentIndexing.form.dateSelect.label')"
          :description="$t('documentIndexing.form.dateSelect.description')"
        >
          <InputDatePicker
            v-model="filingDate"
            class="mt-3"
          />
        </UFormGroup>

      </div>
    </template>
  </FormWrapper>
</template>
<script setup lang="ts">
import { useDocumentIndexing } from '~/composables/useDocumentIndexing'
import { documentTypes } from '~/utils/documentTypes'

const {
  entityId,
  noIdCheckbox,
  documentCategory,
  documentType,
  filingDate
} = useDocumentIndexing()

/**
 * Returns an array of all root keys (categories) from the documentTypes object
 */
function getCategories(): string[] {
  return Object.keys(documentTypes)
}

/**
 * Retrieves document descriptions for the specified category
 * @param category - The category for which to retrieve documents
 * @returns An array of document descriptions or an empty array if the category is not found
 */
function getDocumentsByCategory(category: string): string[]|null {
  const categoryData = documentTypes[category]
  return categoryData ? categoryData.documents.map(doc => doc.description ) : []
}

/**
 * Finds the category based on the prefix of the entity identifier
 * @param identifier - The entity identifier to search
 * @returns The category associated with the prefix or null if no match is found
 */
function findCategoryByPrefix(identifier: string): void {
  const match = identifier.match(/^([A-Za-z]+)\d*/)
  const prefix = match ? match[1].toUpperCase() : '' // Extract prefix

  for (const [category, { prefixes }] of Object.entries(documentTypes)) {
    if (prefixes.includes(prefix)) documentCategory.value = category
  }
}

/** Watch the entity identifier and pre-populate document category when there is a prefix match **/
watch(() => entityId.value, (id: string) => {
  // Format Entity Identifier
  entityId.value = id.replace(/\s+/g, '')?.toUpperCase()
  // Assign and populate a prefix if a match is found
  if (id.length >= 1) findCategoryByPrefix(id)
})

/** Reset Entity Identifier when No Id Checkbox is selected **/
watch(() => noIdCheckbox.value, (hasNoId: boolean) => {
  if (hasNoId) entityId.value = ''
})

</script>