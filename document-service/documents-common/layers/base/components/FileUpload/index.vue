<script setup lang="ts">
import VuePdfEmbed from 'vue-pdf-embed'
import { useFileHandler } from '~/composables/useFileHandler'

/**
 * FileUpload component for handling file uploads with validation.
 * Supports multiple files, drag-and-drop, and displays upload progress.
 *
 * Props:
 * - validate: boolean — Whether to enable validation (default: false)
 * - uploadLabel: string — Label for the upload button (default: 'Upload Files')
 * - multipleFiles: boolean — Allow multiple file selection (default: true)
 * - maxFileSize: number — Maximum file size in bytes (default: 3MB)
 * - acceptedFileTypes: Array of accepted image MIME types (default: [
 *   'application/msword',
 *   'application/vnd.ms-powerpoint',
 *   'application/pdf',
 *   'application/vnd.openxmlformats-officedocument.presentationml.presentation',
 *   'application/vnd.ms-excel',
 *   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
 *   'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
 *   'image/gif',
 *   'image/jpeg',
 *   'image/png',
 *   'image/tiff',
 *   'image/svg+xml',
 *   'text/csv',
 *   'text/plain'
 * ])
 */
const props = defineProps({
  validate: { type: Boolean, default: false },
  uploadLabel: { type: String, default: 'Upload Files' },
  multipleFiles: { type: Boolean, default: true },
  maxFileSize: { type: Number, default: 3 * 1024 * 1024 }, // 3MB
  acceptedFileTypes: { type: Array<string>, default: () => ['application/pdf', 'image/jpeg', 'image/png', 'image/gif'] },
})

/** Emits an event when files are converted */
const emit = defineEmits<{
  (event: 'converted-files', files: any[]): void
}>()

/** Reactive state and methods for file handling */
const {
  state,
  formatBytes,
  removeFile,
  getObjectURL,
  fileHandler
} = useFileHandler({
  maxFileSize: props.maxFileSize,
  acceptedFileTypes: props.acceptedFileTypes,
  onConverted: (files) => emit('converted-files', files)
})

/** Label for the file upload component */
const uploadDescription = computed(() =>
  `Accepted file types: ${props.acceptedFileTypes.map(type => '.' + type.split('/').pop()).join(', ')}.
   Max file size ${formatBytes(props.maxFileSize, 0)}.`
)

/**
 * Computed property to check if there is at least one valid uploaded file.
 * A file is considered valid if it has the `uploaded` property set to true and no `errorMsg`.
 */
const hasValidUploadedFile = computed(() =>
  Array.isArray(state.files) &&
  state.files.some(file => file.uploaded && !file.errorMsg)
)

/**
 * Computed property to determine if a validation error should be shown.
 * Returns true if validation is required and there are no valid uploaded files.
 */
const showValidationError = computed(() =>
  props.validate && !hasValidUploadedFile.value
)
</script>

<template>
  <UForm :state="state" class="w-full" >
    <UFormField name="image">
      <UFileUpload
        v-model="state.files"
        :label="uploadLabel"
        layout="list"
        :multiple="multipleFiles"
        :interactive="false"
        class="w-full"
        @update:model-value="fileHandler"
        :ui="showValidationError ? { label: 'text-red-600', base: 'border-red-600' } : {}"
      >
        <template #leading>{{ null }}</template>
        <template #description>
          <div class="grid">
            <span v-if="showValidationError" class="text-red-600">
              No documents have been uploaded. Please upload the required document.
            </span>
            {{ uploadDescription }}
          </div>
        </template>
        <template #actions="{ open }">
          <div class="flex items-center">
            <UButton
              label="Upload Files"
              icon="i-mdi-file-upload-outline"
              color="primary"
              variant="solid"
              @click="open()"
            />
            <span class="ml-2 text-blue-500 hidden sm:inline">or drag and drop files here</span>
          </div>
        </template>

        <template #file="{ file, index }">
          <div class="w-24">
            <VuePdfEmbed
              v-if="file?.uploaded"
              :source="getObjectURL(file?.document)"
              :page="[1]"
              :width="105"
              :key="file?.document?.name"
            />
            <div v-else class="w-[105px] h-20 rounded bg-gray-100 flex items-center">
              <UIcon
                name="i-mdi-image-outline"
                class="w-7 h-7 m-auto"
              />
            </div>
          </div>

          <div class="w-full ml-4">
            <template v-if="file.errorMsg">
              <div class="flex items-center">
                <UIcon name="i-mdi-close-circle" class="text-red-600 w-5 h-5" />
                <span class="ml-2 text-red-600 text-[14px] italic">
                  Upload of {{file.document?.name}} failed. {{file.errorMsg}}
                </span>
              </div>
            </template>
            <template v-else-if="file?.uploaded">
              <div class="flex items-center">
                <UIcon name="i-mdi-check-circle" class="text-green-700 w-5 h-5" />
                <span class="ml-2 text-[16px] italic">{{ file?.document.name }}</span>
              </div>
              <div class="ml-6">
                {{ formatBytes(file?.document.size, 0) }}
              </div>
            </template>
            <template v-else>
              <UProgress class="w-[200px]" color="primary" />
              <span class="mt-1">Uploading...</span>
            </template>
          </div>

          <UButton
            variant="ghost"
            color="primary"
            @click="removeFile(index)"
            class="w-full sm:w-auto"
          >
            <span>{{ file?.uploaded ? 'Remove' : 'Cancel' }}</span>
            <UIcon name="i-mdi-close" />
          </UButton>
        </template>
      </UFileUpload>
    </UFormField>
  </UForm>
</template>

