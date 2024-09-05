<script setup lang="ts">
import { documentTypes } from '~/utils/documentTypes'
import { useBcrosDocuments } from '~/stores/documents'
const props = defineProps({
  validate: {
    type: Boolean,
    default: false
  }
})
const {
  noIdCheckbox,
  noDocIdCheckbox,
  documentRecord
} = storeToRefs(useBcrosDocuments())

const {
  getDocumentTypesByClass
} = useDocuments()

const hasIdError = computed(() => {
  return props.validate && !documentRecord.value.consumerIdentifier && !noIdCheckbox.value
})
const hasClassError = computed(() => {
  return props.validate && !documentRecord.value.documentClass
})
const hasTypeError = computed(() => {
  return props.validate && !documentRecord.value.documentType
})
const hasDateError = computed(() => {
  return props.validate && !documentRecord.value.consumerFilingDateTime
})

</script>
<template>
  <FormWrapper
    name="record-edit"
    class="mt-7 pb-10"
    data-cy="record-edit"
  >
    <template #label>
      <h3>Document Record Information</h3>
    </template>

    <template #form>
      <div class="grid grid-flow-row auto-rows-max">
        <!-- Document Id -->
        <UFormGroup
          :label="$t('documentIndexing.form.docId.label')"
          :description="$t('documentIndexing.form.docId.description')"
          :help="$t('documentIndexing.form.docId.help')"
          :error="hasIdError && 'Enter Document ID'"
        >
          <UInput
            v-model="documentRecord.consumerDocumentId"
            class="mt-3"
            type="text"
            required
            :disabled="noDocIdCheckbox"
            :placeholder="$t('documentIndexing.form.docId.label')"
            :ui="{ placeholder: hasIdError ? 'placeholder:text-red-500' : 'text-gray-700' }"
          />
        </UFormGroup>

        <UCheckbox
          v-model="noDocIdCheckbox"
          class="mt-5"
          name="unknown-id-checkbox"
          :label="$t('documentIndexing.form.docIdCheckbox.label')"
        />

        <UDivider class="my-7" />

        <!-- Entity ID -->
        <UFormGroup
          :label="$t('documentIndexing.form.id.label')"
          :description="$t('documentIndexing.form.id.description')"
          :help="$t('documentIndexing.form.id.help')"
          :error="hasIdError && 'Enter entity ID'"
        >
          <UInput
            v-model="documentRecord.consumerIdentifier"
            class="mt-3"
            type="text"
            required
            :disabled="noIdCheckbox"
            :placeholder="$t('documentIndexing.form.id.label')"
            :ui="{ placeholder: hasIdError ? 'placeholder:text-red-500' : 'text-gray-700' }"
          />
        </UFormGroup>

        <UCheckbox
          v-model="noIdCheckbox"
          class="mt-5"
          name="unknown-id-checkbox"
          :label="$t('documentIndexing.form.checkbox.label')"
        />

        <UDivider class="my-7" />

        <UFormGroup
          :label="$t('documentIndexing.form.selectMenu.label')"
        >
          <div class="grid grid-cols-4 gap-5 mt-3">
            <div class="col-span-2">
              <UFormGroup :error="hasClassError && 'Select document category'">
                <USelectMenu
                  v-model="documentRecord.documentClass"
                  :placeholder="$t('documentIndexing.form.selectMenu.categoryLabel')"
                  select-class="text-gray-700"
                  :options="documentTypes"
                  value-attribute="class"
                  option-attribute="description"
                  :ui="{ placeholder: hasClassError ? 'placeholder:text-red-500' : 'text-gray-700' }"
                />
              </UFormGroup>
            </div>

            <div class="col-span-2">
              <UFormGroup :error="hasTypeError && 'Select document type'">
                <USelectMenu
                  v-model="documentRecord.documentType"
                  :placeholder="$t('documentIndexing.form.selectMenu.typeLabel')"
                  select-class="text-gray-700"
                  :disabled="!documentRecord.documentClass"
                  :options="getDocumentTypesByClass(documentRecord.documentClass)"
                  value-attribute="type"
                  option-attribute="description"
                  :ui="{ placeholder: hasTypeError ? 'placeholder:text-red-500' : 'text-gray-700' }"
                />
              </UFormGroup>
            </div>
          </div>
        </UFormGroup>

        <UDivider class="my-7" />

        <UFormGroup
          :label="$t('documentIndexing.form.description.label')"
          :error="hasDateError && 'Select a filing date'"
          :help="$t('documentIndexing.form.description.help')"
        >
          <UTextarea
            v-model="documentRecord.documentDescription"
            class="mt-3"
            required
            :placeholder="$t('documentIndexing.form.description.placeholder')"
          />
        </UFormGroup>

        <UDivider class="my-7" />

        <UFormGroup
          :label="$t('documentIndexing.form.dateSelect.label')"
          :description="$t('documentIndexing.form.dateSelect.description')"
          :error="hasDateError && 'Select a filing date'"
        >
          <InputDatePicker
            v-model="documentRecord.consumerFilingDateTime"
            class="mt-3"
            :ui="{ placeholder: hasDateError ? 'placeholder:text-red-500' : 'text-gray-700' }"
          />
        </UFormGroup>

      </div>
    </template>
  </FormWrapper>
</template>
<style scoped lang="scss">
</style>