import { useBcrosDocuments } from '~/stores/documents'
import { postDocument } from '~/utils/documentRequests'
import type { ApiResponseOrError } from '~/interfaces/request-interfaces'
import type { DocumentInfoIF } from '~/interfaces/document-types-interface'

export const useDocumentIndexing = () => {
  const {
    consumerIdentifier,
    documentClass,
    documentType,
    consumerFilingDate,
    documentList,
    validateIndex,
    isLoading,
    documentInfoRO,
    displayDocumentReview
  } = storeToRefs(useBcrosDocuments())

  /** Initialize Document Indexing */
  const initDocumentState = () => {
    validateIndex.value = false
    consumerIdentifier.value = ''
    documentClass.value = ''
    documentType.value = ''
    consumerFilingDate.value = ''
    documentList.value = []
    validateIndex.value = false
    isLoading.value = false
    displayDocumentReview.value = false
    documentInfoRO.value = null
  }

  /** Computed validation flag to check for required document meta data **/
  const isValidIndexData = computed(() => {
    return !!consumerIdentifier.value
      && !!documentClass.value
      && !!documentType.value
      && !!consumerFilingDate.value
  })

  /** Validate and Save Document Indexing */
  const saveDocuments = async (): Promise<void> => {
    // Validate Document Indexing
    validateIndex.value = true

    if (isValidIndexData.value) {
      isLoading.value = true

      // Initialize an object to hold the consolidated data
      const consolidatedResponse = {
        data: null as DocumentInfoIF,
        fileNames: [] as string[],
        consumerDocumentId: '', // To store the consumerDocumentID from the first request
      }

      try {
        // Iterate over the document list and handle requests sequentially
        for (const document of documentList.value) {
          const response: ApiResponseOrError = await postDocument(
            {
              consumerIdentifier: consumerIdentifier.value,
              documentClass: documentClass.value,
              documentType: documentType.value,
              consumerFilingDate: formatDateToISO(consumerFilingDate.value),
              consumerFilename: document.name,
              // If a consumerDocumentId is needed for subsequent requests, it can be added here
              ...(consolidatedResponse.consumerDocumentId && {
                consumerDocumentId: consolidatedResponse.consumerDocumentId
              })
            },
            document
          )

          if ('data' in response) {
            // Store the data only once (assuming all successful responses have identical data)
            if (!consolidatedResponse.data) {
              consolidatedResponse.data = response.data.value
              // Store the consumerDocumentId from the first request
              consolidatedResponse.consumerDocumentId = response.data.value.consumerDocumentId
            }

            // Add the document name to the fileNames array
            consolidatedResponse.fileNames.push(document.name)

            // Will remove post POC
            console.warn('Success:', response.data.value)
          } else {
            // Will remove post POC
            console.warn('Error:', response.message, response.status, response.statusText)
            isLoading.value = false
            return // Exit if there is an error in any request
          }
        }

        // Store the consolidated result after all requests have completed
        documentInfoRO.value = { ...consolidatedResponse.data, filenames: consolidatedResponse.fileNames }

        // Display the document review
        isLoading.value = false
        displayDocumentReview.value = true
      } catch (error) {
        console.error('Request failed:', error)
        isLoading.value = false
      }
    }
  }

  return {
    initDocumentState,
    isValidIndexData,
    saveDocuments
  }
}
