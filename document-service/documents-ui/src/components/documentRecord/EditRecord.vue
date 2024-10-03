<script setup lang="ts">
import { documentTypes } from '~/utils/documentTypes'
import { useBcrosDocuments } from '~/stores/documents'
import EditScanning from '~/components/documentRecord/EditScanning.vue'
import { formatDateToISO } from '~/utils/dateHelper'
const emit = defineEmits(['closeEdit'])
defineProps({
  validate: {
    type: Boolean,
    default: false
  }
})
const {
  validateRecordEdit,
  noIdCheckbox,
  documentRecord,
  documentRecordSnapshot
} = storeToRefs(useBcrosDocuments())

const { getDocumentTypesByClass } = useDocuments()

const hasIdError = computed(() => {
  return validateRecordEdit.value && !documentRecord.value.consumerIdentifier && !noIdCheckbox.value
})
const hasClassError = computed(() => {
  return validateRecordEdit.value && !documentRecord.value.documentClass
})
const hasTypeError = computed(() => {
  return validateRecordEdit.value && !documentRecord.value.documentType
})
const hasDateError = computed(() => {
  return validateRecordEdit.value && !documentRecord.value.consumerFilingDateTime
})
const hasDescriptionError = computed(() => {
  return documentRecord.value.description?.length > 1000
})

/** Reset Entity Identifier when No Id Checkbox is selected **/
watch(() => noIdCheckbox.value, (hasNoId: boolean) => {
  if (hasNoId) documentRecord.value.consumerIdentifier = ''
})
/** Reset Document Type when Document Class is changed **/
watch(() => documentRecord.value.documentClass, () => {
  documentRecord.value.documentType = ''
})
documentRecord.documentClass

</script>
<template>
  <div data-cy="record-edit">
    <ContentWrapper class="pb-10 pa-0 ma-0">
      <template #header>
        <div class="flex justify-between">
          <div class="flex">
            <UIcon name="i-mdi-text-box" class="w-6 h-6 text-blue-350" />
            <div class="ml-2">{{ $t('documentRecord.subtitle') }}</div>
          </div>
          <div>
            <UButton
              variant="ghost"
              icon="i-mdi-close"
              :label="$t('documentRecord.cancelButton')"
              data-cy="edit-record-button"
              @click="emit('closeEdit')"
            />
          </div>
        </div>
      </template>
      <template #content>
        <!-- Document Record Information Form -->
        <FormWrapper
          name="record-edit"
          class="pl-2 pt-2"
          data-cy="record-edit-form"
        >
          <template #label>
            <h3>Document Record Information</h3>
          </template>

          <template #form>
            <div class="grid grid-flow-row auto-rows-max">
              <!-- Document Id -->
              <UFormGroup :label="$t('documentIndexing.form.docId.label')">
                <UInput
                  v-model="documentRecord.consumerDocumentId"
                  class="mt-3"
                  type="text"
                  required
                  :disabled="true"
                  :placeholder="$t('documentIndexing.form.docId.label')"
                  :ui="{ base: 'disabled:opacity-100 disabled:border-dotted' }"
                />
              </UFormGroup>

              <UDivider class="my-7" />

              <!-- Entity ID -->
              <UFormGroup
                :label="$t('documentIndexing.form.id.label')"
                :description="$t('documentIndexing.form.id.description')"
                :help="$t('documentIndexing.form.id.help')"
                :error="hasIdError && 'Enter entity ID'"
              >
                <template #label>
                  <span class="flex">
                    {{ $t('documentIndexing.form.id.label') }}
                    <HasChangesBadge
                      class="ml-1"
                      :baseline="documentRecordSnapshot.consumerIdentifier"
                      :current-state="documentRecord.consumerIdentifier"
                    />
                  </span>
                </template>

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

              <UFormGroup :label="$t('documentIndexing.form.selectMenu.label')">
                <template #label>
                  <span class="flex">
                    {{ $t('documentIndexing.form.selectMenu.label') }}
                    <HasChangesBadge
                      class="ml-1"
                      :baseline="{
                        class: documentRecordSnapshot.documentClass,
                        type: documentRecordSnapshot.documentType
                      }"
                      :current-state="{
                        class: documentRecord.documentClass,
                        type: documentRecord.documentType
                      }"
                    />
                  </span>
                </template>

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
                :error="hasDescriptionError && 'Exceeded 1000 characters'"
              >
                <template #label>
                  <span class="flex">
                    {{ $t('documentIndexing.form.description.label') }}
                    <HasChangesBadge
                      class="ml-1"
                      :baseline="documentRecordSnapshot.description"
                      :current-state="documentRecord.description"
                    />
                  </span>
                </template>

                <UTextarea
                  v-model="documentRecord.description"
                  class="mt-3"
                  required
                  :placeholder="$t('documentIndexing.form.description.placeholder')"
                />
                <span class="mt-1 float-right text-sm text-gray-700">{{documentRecord.description?.length}}/1000</span>
              </UFormGroup>

              <UDivider class="my-7" />

              <UFormGroup
                :label="$t('documentIndexing.form.dateSelect.label')"
                :description="$t('documentIndexing.form.dateSelect.description')"
                :error="hasDateError && 'Select a filing date'"
              >
                <template #label>
                  <span class="flex">
                    {{ $t('documentIndexing.form.dateSelect.label') }}
                    <HasChangesBadge
                      class="ml-1"
                      :baseline="formatDateToISO(documentRecordSnapshot?.consumerFilingDateTime)"
                      :current-state="formatDateToISO(documentRecord?.consumerFilingDateTime)"
                    />
                  </span>
                </template>

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
    </ContentWrapper>

    <!-- Document Scanning Edit -->
    <EditScanning class=" bg-white rounded" />

    <!-- Document Upload Edit -->
    <DocumentUpload class="mt-10 bg-white rounded" />
  </div>
</template>