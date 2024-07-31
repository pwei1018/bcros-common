<template>
  <FormWrapper name="'document-upload'">
    <template #label>
      <h3>Upload Documents</h3>
    </template>

    <template #form>
      <UFormGroup
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
            @change="uploadFile"
          />
        </div>
      </UFormGroup>

      <section class="mt-6 ml-1">
        <div
          v-for="(supportingDocument, index) in documents"
          :key="supportingDocument.name"
        >
          <div class="flex flex-row items-center mt-2">
            <img
              class="mr-1 h-[18px] w-[18px]"
              src="~/assets/icons/attach_dark.svg"
              alt="Attach icon"
            >
            <span>{{ supportingDocument.name }}</span>
            <UIcon
              name="i-mdi-delete"
              class="h-[18px] w-[18px] ml-1 cursor-pointer"
              @click="() => removeFile(index)"
            />
          </div>
        </div>
      </section>

    </template>
  </FormWrapper>
</template>

<script setup lang="ts">
const { documents } = useDocumentIndexing()
const t = useNuxtApp().$i18n.t

const fileError = ref(null)

const uploadFile = (file: FileList) => {
  if (!file.length) return
  const extension = file[0].name.substring(file[0].name.length - 3)
  const validType = ['pdf']
  const fileSize = file[0].size / 1024 / 1024 // in MiB
  const validFileType = validType.includes(extension)
  const validFileSize = fileSize <= 50
  if (!validFileSize) {
    fileError.value = t('documentUpload.fileSizeError')
  } else if (!validFileType) {
    fileError.value = t('documentUpload.fileTypeError')
  } else {
    fileError.value = null
    documents.value.push(file[0])
  }
}

const removeFile = (index: number) => {
  documents.value.splice(index, 1)
}
</script>