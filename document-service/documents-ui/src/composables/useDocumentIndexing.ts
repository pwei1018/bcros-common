import { useBcrosDocuments } from '~/stores/documents'

export const useDocumentIndexing = () => {
  const {
    consumerIdentifier,
    documentClass,
    documentType,
    consumerFilingDate,
    documentList,
    validateIndex
  } = storeToRefs(useBcrosDocuments())

  /** Validate and Save Document Indexing */
  const initDocumentState = () => {
    validateIndex.value = false
    consumerIdentifier.value = ''
    documentClass.value = ''
    documentType.value = ''
    consumerFilingDate.value = ''
    documentList.value = []
  }

  /** Computed validation flag to check for required document meta data **/
  const isValidIndexData = computed(() => {
    return !!consumerIdentifier.value
      && !!documentClass.value
      && !!documentType.value
      && !!consumerFilingDate.value
  })

  /** Validate and Save Document Indexing */
  const saveDocuments = () => {
    // Validate Document Indexing
    validateIndex.value = true

    if (isValidIndexData.value) {
      // Save document indexing: Future
      const documentIndexing = {
        consumerIdentifier: consumerIdentifier.value,
        documentClass: documentClass.value,
        documentType: documentType.value,
        consumerFilingDate: consumerFilingDate.value,
        documents: documentList.value
      }

      console.warn('Document Indexing:', documentIndexing)
    }
  }

  return {
    initDocumentState,
    isValidIndexData,
    saveDocuments
  }
}
