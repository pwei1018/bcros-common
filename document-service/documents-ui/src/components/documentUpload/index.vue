<script setup lang="ts">
defineProps({
  validate: {
    type: Boolean,
    default: false
  }
})

const { isEditing, documentList, documentListSnapshot } = storeToRefs(useBcrosDocuments())
const t = useNuxtApp().$i18n.t
const fileError = ref(null)

/**
 * Uploads valid PDF files to the documents array.
 * @param {FileList} files - The list of files to be uploaded.
 */
const uploadFile = (files: FileList) => {
  const validType = ['pdf']
  const maxFileSizeMiB = 50

  // Convert FileList to Array
  const allFiles = Array.from(files)

  // Validate each file
  const invalidFile = allFiles.find(file => {
    const extension = file.name.slice(-3).toLowerCase()
    const fileSize = file.size / 1024 / 1024 // in MiB
    const validFileType = validType.includes(extension)
    const validFileSize = fileSize <= maxFileSizeMiB

    if (!validFileSize) {
      fileError.value = t('documentUpload.fileSizeError')
      return true
    } else if (!validFileType) {
      fileError.value = t('documentUpload.fileTypeError')
      return true
    }
    return false
  })

  // If all files are valid, add them to the documents array
  if (!invalidFile) {
    fileError.value = null
    documentList.value.push(...allFiles)
  }
}

/** Remove a file from the documents array. */
const removeFile = (index: number) => {
  documentList.value.splice(index, 1)
}
</script>
<template>
  <FormWrapper
    name="document-upload"
    class="pl-7"
  >
    <template #label>
      <h3>Upload Documents</h3>
      <HasChangesBadge
        v-if="isEditing"
        :baseline="documentListSnapshot"
        :current-state="documentList"
      />
    </template>

    <template #form>
      <UFormGroup
        :ui="{ help: 'ml-9', error: 'ml-9' }"
        :description="$t('documentUpload.description')"
        :help="$t('documentUpload.help')"
        :error="fileError"
      >
        <div class="flex flex-row">
          <img class="mr-3" src="~/assets/icons/attach.svg" alt="Paperclip icon">
          <UInput
            id="inputFile"
            accept=".pdf"
            class="mt-3 text-gray-200 w-full"
            content="text-gray-700"
            :placeholder="$t('documentUpload.placeholder')"
            type="file"
            multiple
            @change="uploadFile"
          />
        </div>
      </UFormGroup>

      <section v-if="documentList.length" class="mt-6">
        <div
          v-for="(supportingDocument, index) in documentList"
          :key="supportingDocument.name"
        >
          <div class="flex justify-between mt-2 pl-4 rounded items-center bg-bcGovColor-ltBlue h-[50px] text-gray-900">
            <div class="flex">
              <img
                class="mr-2 h-[18px] w-[18px]"
                src="~/assets/icons/attach_dark.svg"
                alt="Attach icon"
              >
              <span>{{ supportingDocument.name }}</span>
            </div>
            <UButton
              class="py-2 px-6 text-base font-normal float-right"
              color="primary"
              variant="ghost"
              @click="removeFile(index)"
            >
              Remove
              <UIcon
                name="i-mdi-close"
                class="h-[18px] w-[18px] ml-1"
              />
            </UButton>
          </div>
        </div>
      </section>

    </template>
  </FormWrapper>
</template>