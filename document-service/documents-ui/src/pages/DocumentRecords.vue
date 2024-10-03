<script setup lang="ts">
import EditRecord from '~/components/documentRecord/EditRecord.vue'
import { scrollToTop } from '~/utils/commonUtils'
const { updateDocuments, isValidRecordEdit, retrieveDocumentRecord, hasDocumentRecordChanges } = useDocuments()
const {
  isLoading,
  isEditing,
  isEditingReview,
  validateRecordEdit
} = storeToRefs(useBcrosDocuments())

/**
 * onMounted hook to initialize document state:
 * - Disables editing mode.
 * - Fetches document record.
 * - Logs errors and redirects to document management on failure.
 */
onMounted(async () => {
  // Toggle Editing
  isEditing.value = false
  isLoading.value = true
  try {
    await retrieveDocumentRecord(identifier)
    isLoading.value = false
  } catch (error) {
    console.error('Error fetching document record', error)
    navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
    isLoading.value = false
  }
})

const showDialog = ref(false)
const identifier = useRoute()?.params?.identifier as string

const cancel = (forceCancel: boolean = false) => {
  if(hasDocumentRecordChanges.value && !forceCancel) {
    showDialog.value = true
  } else {
    isEditing.value = false
    isEditingReview.value = false
    validateRecordEdit.value = false
    showDialog.value = false
  }
}

const back = () => {
  isEditingReview.value = false
  validateRecordEdit.value = false
  scrollToTop()
}

const next = async () => {
  if (isEditingReview.value) {
    // Save document record here
    await updateDocuments()

    navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
    isEditing.value = false
    isEditingReview.value = false
  } else {
    if (!hasDocumentRecordChanges.value) {
      scrollToTop()
    } else {
      validateRecordEdit.value = true
      if (isValidRecordEdit.value) {
        isEditingReview.value = true
      }
      scrollToTop()
    }
  }
}

/** Watch the isEditing flag and re-populate document record when editing is ended **/
watch(() => isEditing.value, async (val: boolean) => {
  if (!val) await retrieveDocumentRecord(identifier)
})
</script>
<template>
  <div
    id="document-records"
    data-cy="document-records"
    class="min-h-[800px]"
  >
    <div class="app-inner-container app-body">

      <ConfirmationModal
        :toggle-modal="showDialog"
        @close="showDialog = false"
        @confirm="cancel(true)"
      />

      <div class="grid grid-cols-8 gap-4 mt-10 mb-16">
        <div
          v-if="!isLoading || isEditingReview"
          class="col-span-6"
        >
          <!-- Document Review Content Headers -->
          <div
            v-if="isEditingReview"
            class="mb-8"
          >
            <span class="text-gray-900 text-[32px] font-bold">Review and Confirm</span>
            <p class="text-gray-700 mt-1">Review your document record details before saving.</p>
          </div>

          <!-- Document Record Information -->
          <DocumentRecord
            v-if="!isEditing || isEditingReview"
            :is-review-mode="isEditingReview"
            @open-edit="isEditing = true"
          />

          <!-- Edit Document Record -->
          <EditRecord
            v-else
            @close-edit="cancel"
          />
        </div>

        <div class="col-span-2"/>
      </div>
    </div>
    <NavFooter
      v-if="isEditing"
      cancel-btn="Cancel"
      :back-btn="isEditingReview ? 'Back' : ''"
      next-btn="Review and Confirm"
      @cancel="cancel"
      @back="back"
      @next="next"
    />
  </div>
</template>