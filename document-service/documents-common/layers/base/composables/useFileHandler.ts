// documents-ui/layers/base/composables/useFileHandler.ts
import { ref, reactive } from 'vue'
import * as z from 'zod'
import { pdfConversion } from '~/utils/drsRequests'
import type { FileHandlerOptionsIF } from '~/interfaces/file-interfaces'

/**
 * Composable for handling file uploads, validation, and PDF conversion.
 * @param {FileHandlerOptionsIF} options - Configuration options for file handling.
 * @returns {object} File handler state, schema, and utility methods.
 */
export function useFileHandler(options: FileHandlerOptionsIF = {}) {
  // Destructure options
  const {
    maxFileSize,
    minDimensions,
    maxDimensions,
    acceptedFileTypes,
  } = options

  /**
   * Formats bytes as a human-readable string.
   * @param {number} bytes - The number of bytes.
   * @param {number} decimals - Number of decimal places.
   * @returns {string} Formatted string.
   */
  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
  }

  /**
   * Zod schema for file validation.
   */
  const schema = z.object({
    file: z
      .instanceof(File, { message: 'Please select a file.' })
      .refine((file) => file.size <= maxFileSize, {
        message: `The file is too large. Please choose an image smaller than ${formatBytes(maxFileSize)}.`
      })
      .refine((file) => acceptedFileTypes.includes(file.type), {
        message: `Please upload a valid file
        (${acceptedFileTypes.map(type => type.split('/').pop()?.toUpperCase()).join(', ')}).`
      })
      .refine(
        (file) =>
          new Promise((resolve) => {
            const reader = new FileReader()
            reader.onload = (e) => {
              const img = new Image()
              img.onload = () => {
                const meetsDimensions =
                  img.width >= minDimensions.width &&
                  img.height >= minDimensions.height &&
                  img.width <= maxDimensions.width &&
                  img.height <= maxDimensions.height
                resolve(meetsDimensions)
              }
              img.src = e.target?.result as string
            }
            reader.readAsDataURL(file)
          }),
        {
          message: `The image dimensions are invalid. Please upload an image between ${minDimensions.width}x${minDimensions.height} and ${maxDimensions.width}x${maxDimensions.height} pixels.`
        }
      )
  })

  /** Reactive state for file handling. */
  const state = reactive<{ files?: any[] }>({ files: undefined })

  /** Indicates if a file operation is in progress. */
  const isProcessing = ref(false)

  /**
   * Removes a file from the state by index.
   * @param {number} index - Index of the file to remove.
   */
  const removeFile = (index: number) => {
    if (Array.isArray(state.files)) {
      state.files.splice(index, 1)

      // Call emit event with the updated files
      options.onConverted(state.files.map(f => f.document))
    }
  }

  /**
   * Converts a file to PDF using the pdfConversion utility.
   * @param {File} file - The file to convert.
   * @returns {Promise<File>} The converted PDF file.
   */
  const convertPdf = async (file: File) => {
    const blobResponse = await pdfConversion(file)
    if (blobResponse.status === 'error') {
      throw new Error('Failed to convert file to PDF. No Blob returned.')
      return
    }
    return new File(
      [blobResponse],
      file.name.replace(/\.[^/.]+$/, '.pdf'),
      { type: 'application/pdf' }
    )
  }

  /**
   * Returns an object URL for a given file.
   * @param {File} file - The file to create an object URL for.
   * @returns {string | undefined} The object URL.
   */
  const getObjectURL = (file: File) => window.URL?.createObjectURL(file)

  /**
   * Handles file uploads, validation, and conversion.
   * @param {File[]} files - Array of files to handle.
   */
  const fileHandler = async (files: File[]) => {
    if (isProcessing.value) return
    isProcessing.value = true
    const fileArray = Array.isArray(files) ? files : [files]
    if (!Array.isArray(state.files)) state.files = state.files ? [state.files] : []
    try {
      for (const [index, file] of fileArray.entries()) {
        // Only process files that haven't been uploaded yet
        if (!file.uploaded) {
          try {
            const document = await convertPdf(file)
            state.files[index] = {
              document,
              uploaded: true,
              index
            }

            // Call emit event with the updated files
            options.onConverted(state.files.map(f => f.document))
          } catch (error) {
            console.error(`Error converting file at index ${index}:`, error)
            state.files[index] = {
              uploaded: false,
              errorMsg: 'Failed to convert file to PDF.'
            }
          }
        }
      }
    } finally {
      isProcessing.value = false
    }
  }

  return {
    state,
    schema,
    isProcessing,
    formatBytes,
    removeFile,
    convertPdf,
    getObjectURL,
    fileHandler
  }
}
