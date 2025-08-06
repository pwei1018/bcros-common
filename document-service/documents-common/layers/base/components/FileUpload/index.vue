<script setup lang="ts">
import VuePdfEmbed from 'vue-pdf-embed'
import { useFileHandler } from '~/composables/useFileHandler'

/**
 * FileUpload component for handling file uploads with validation.
 * It supports multiple files, drag-and-drop, and displays upload progress.
 *
 * Props:
 * - maxFileSize: Maximum file size in bytes (default: 3MB)
 * - minDimensions: Minimum dimensions for image files (default: { width: 300, height: 300 })
 * - maxDimensions: Maximum dimensions for image files (default: { width: 2048, height: 2048 })
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
  uploadLabel: { type: String, default: 'Upload Files' },
  multipleFiles: { type: Boolean, default: true },
  maxFileSize: { type: Number, default: 3 * 1024 * 1024 }, // 3MB
  minDimensions: { type: Object, default: () => ({ width: 300, height: 300 }) },
  maxDimensions: { type: Object, default: () => ({ width: 2048, height: 2048 }) },
  acceptedFileTypes: { type: Array, default: () => ['application/pdf', 'image/jpeg', 'image/png', 'image/gif'] },
})

/** Emits an event when files are converted */
const emit = defineEmits<{
  (event: 'converted-files', files: any[]): void
}>()

/** Reactive state and methods for file handling */
const {
  state,
  schema,
  formatBytes,
  removeFile,
  getObjectURL,
  fileHandler
} = useFileHandler({
  maxFileSize: props.maxFileSize,
  minDimensions: props.minDimensions,
  maxDimensions: props.maxDimensions,
  acceptedFileTypes: props.acceptedFileTypes,
  onConverted: (files) => emit('converted-files', files)
})

/** Label for the file upload component */
const uploadDescription = computed(() =>
  `Accepted file types: ${props.acceptedFileTypes.map(type => '.' + type.split('/').pop()).join(', ')}.
  Max file size ${formatBytes(props.maxFileSize, 0)}.`
)
</script>

<template>
  <UForm :schema="schema" :state="state" class="w-full" >
    <UFormField name="image">
      <UFileUpload
        v-model="state.files"
        :label="uploadLabel"
        :description="uploadDescription"
        layout="list"
        :multiple="multipleFiles"
        :interactive="false"
        class="w-full"
        @update:model-value="fileHandler"
      >
        <template #leading>{{ null }}</template>
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
              :height="100"
            />
            <div v-else class="w-20 h-17 rounded bg-gray-100 flex items-center">
              <UIcon
                name="i-mdi-image-outline"
                class="w-7 h-7 m-auto"
              />
            </div>
          </div>

          <div class="w-full ml-2">
            <template v-if="file.errorMsg">
              {{file.errorMsg}}
            </template>
            <template v-else-if="file?.uploaded">
              <div class="flex items-center">
                <UIcon name="i-mdi-check-circle" class="text-green-700 w-5 h-5" />
                <span class="ml-1">{{ file?.document.name }}</span>
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

