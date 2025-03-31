<script setup lang="ts">
import { useBcrosDocuments } from '~/stores/documents'
const props = defineProps({
  validate: {
    type: Boolean,
    default: false
  }
})

const {
  consumerDocumentId,
  consumerIdentifier,
  noIdCheckbox,
  noDocIdCheckbox,
  documentClass,
  documentType,
  description,
  consumerFilingDate,
  isValidDocId
} = storeToRefs(useBcrosDocuments())

const {
  findCategoryByPrefix,
  getDocumentTypesByClass
} = useDocuments()

const isDocIdLoading = ref(false)
const docIdError = ref('')

const hasIdError = computed(() => {
  return props.validate && !consumerIdentifier.value && !noIdCheckbox.value
})
const hasClassError = computed(() => {
  return props.validate && !documentClass.value
})
const hasTypeError = computed(() => {
  return props.validate && documentClass.value && !documentType.value
})
const hasDescriptionError = computed(() => {
  return description.value.length > 1000
})

const docIdTrailingIcon = computed(() => {
  if (docIdError.value !== '' || consumerDocumentId.value.length === 0) return ""
  if (isDocIdLoading.value) return "i-mdi-loading"
  return "i-mdi-check"
})

/** Watch the document ID for validation and update the error message accordingly. */
watch(() => consumerDocumentId.value.trim(), async (docId: string) => {
  if (docId && !/^\d+$/.test(docId)) {
    docIdError.value = "Must contain numbers only"
    return
  }
  if (docId.length < 8 && !noDocIdCheckbox.value) {
    docIdError.value = "Enter the 8-digit Document ID number, also referred to as the barcode number"
    return
  } 
  docIdError.value = ""
  isDocIdLoading.value = true
  const response = await verifyDocumentId(docId)
  
  if (response.status.value === 'success' && Array.isArray(response.data.value)) {
    docIdError.value = "A document record already exists with this document ID. "
    isValidDocId.value = false
  } else if (response?.statusCode === 400){
    docIdError.value = "Document ID check digit failed"
    isValidDocId.value = false
  } else if (response?.statusCode === 404) {
    isValidDocId.value = true
  }
  isDocIdLoading.value = false
})

/** Watch the entity identifier and pre-populate document category when there is a prefix match **/
watch(() => consumerIdentifier.value, (id: string) => {
  // Format Entity Identifier
  consumerIdentifier.value = id.replace(/\s+/g, '')?.toUpperCase()
  // Assign and populate a prefix if a match is found
  if (id.length >= 1) findCategoryByPrefix(id)
})

/** Reset Entity Identifier when No Id Checkbox is selected **/
watch(() => noIdCheckbox.value, (hasNoId: boolean) => {
  if (hasNoId) consumerIdentifier.value = ''
})

/** Reset Document Identifier when No Doc Id Checkbox is selected **/
watch(() => noDocIdCheckbox.value, (hasNoDocId: boolean) => {
  if (hasNoDocId) {
    consumerDocumentId.value = ''
    isValidDocId.value = true
  }
})

/** Reset Document Type when Category Changes **/
watch(() => documentClass.value, () => {
 documentType.value = ''
})
</script>
<template>
  <FormWrapper
    id="document-indexing-form"
    name="document-indexing-form"
    class="rounded"
  >
    <template #label>
      <h2 class="text-base leading-6 font-bold pr-8">{{ $t('documentIndexing.label') }}</h2>
    </template>

    <template #form>
      <div class="grid grid-flow-row auto-rows-max">
        <UFormGroup
          :label="$t('documentIndexing.form.docId.label')"
          :description="$t('documentIndexing.form.docId.description')"
          :error="docIdError"
        >
          <UInput
            v-model="consumerDocumentId"
            class="mt-3"
            type="text"
            maxlength="8"
            required
            :disabled="noDocIdCheckbox"
            :placeholder="$t('documentIndexing.form.docId.label')"
            :ui="{ placeholder: docIdError ? 'placeholder:text-red-500' : 'text-gray-700' }"
          >
          <template #trailing>
            <UIcon
              v-show="docIdTrailingIcon"
              :name="docIdTrailingIcon"
              :class="['w-5 h-5 ml-1', isDocIdLoading ? 'animate-spin' : 'text-green-700']"
            />
        </template>
          </UInput>
        </UFormGroup>
        <div class="mt-5 flex">
          <UCheckbox
          v-model="noDocIdCheckbox"
          name="unknown-docId-checkbox"
          :label="$t('documentIndexing.form.docIdCheckbox.label')"
        />
          <UTooltip
            :popper="{ placement: 'top', arrow: true }"
            :text="$t('documentIndexing.form.docIdCheckbox.tooltip')"
            :ui="{ base: 'w-[265px]' }"
          >
            <UIcon
              name="i-mdi-information-outline"
              class="w-5 h-5 ml-1 text-primary"
            />
          </UTooltip>
        </div>
        
        <UDivider class="my-7" />

        <UFormGroup
          :label="$t('documentIndexing.form.id.label')"
          :description="$t('documentIndexing.form.id.description')"
          :help="$t('documentIndexing.form.id.help')"
          :error="hasIdError && 'Enter entity ID'"
        >
          <UInput
            v-model="consumerIdentifier"
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
              <UFormGroup :error="hasClassError && 'This field is required'">
                <EntityTypeSelector v-model="documentClass" />
              </UFormGroup>
            </div>

            <div class="col-span-2">
              <UFormGroup :error="hasTypeError && 'Select document type'">
                <USelectMenu
                  v-model="documentType"
                  :placeholder="$t('documentIndexing.form.selectMenu.typeLabel')"
                  select-class="text-gray-700"
                  :disabled="!documentClass"
                  :options="getDocumentTypesByClass(documentClass)"
                  value-attribute="type"
                  option-attribute="description"
                  :ui="{ placeholder: hasTypeError ? 'placeholder:text-red-500' : 'text-gray-700' }"
                >
                <template #trailing>
                  <UIcon name="i-mdi-arrow-drop-down" class="w-5 h-5 " />
                </template>
                <template #option="{ option, selected }">
                  <span :class="selected ? '' : 'text-gray-700'">
                    {{ option.description }}
                  </span>
                </template>
              </USelectMenu>
              </UFormGroup>
            </div>
          </div>
        </UFormGroup>

        <UDivider class="my-7" />

        <UFormGroup
          :label="$t('documentIndexing.form.description.label')"
          :error="hasDescriptionError && 'Exceeded 1000 characters'"
        >
          <UTextarea
            v-model="description"
            class="mt-3"
            required
            :placeholder="$t('documentIndexing.form.description.placeholder')"
          />
          <span class="mt-1 float-right text-sm text-gray-700">{{description.length}}/1000</span>
        </UFormGroup>

        <UDivider class="my-7" />

        <UFormGroup
          :label="$t('documentIndexing.form.dateSelect.label')"
          :description="$t('documentIndexing.form.dateSelect.description')"
        >
          <InputDatePicker
            v-model="consumerFilingDate"
            class="mt-3"
            :date-placeholder="$t('documentIndexing.form.dateSelect.placeholder')"
            :ui="{ placeholder: 'text-gray-700' }"
            :is-trailing="true"
          />
        </UFormGroup>

      </div>
    </template>
  </FormWrapper>
</template>