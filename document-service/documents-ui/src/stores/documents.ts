import type { DocumentInfoIF, DocumentStateIF } from '~/interfaces/document-types-interface'

export const useBcrosDocuments = defineStore('bcros/documents', () => {

  // Function to return default values
  const getDefaultState = (): DocumentStateIF => ({
    // Document Search
    searchDocumentId: '',
    searchEntityId: '',
    searchDocumentClass: '',
    searchDocumentType: '',
    searchDateRange: { start: null, end: null },

    // Document Meta
    consumerIdentifier: '',
    noIdCheckbox: false,
    noDocIdCheckbox: false,
    documentClass: '',
    documentType: '',
    consumerFilingDate: '',
    documentList: [],

    // Validations
    validateIndex: false,
    isLoading: false,
    validateDocumentSearch: false,

    // Document Review
    displayDocumentReview: false,
    documentInfoRO: null as DocumentInfoIF,
    documentSearchResults: [],
    documentRecord: null
  })

  // Initial state
  const state = reactive(getDefaultState())

  // Reset state function
  const resetStore = () => {
    Object.assign(state, getDefaultState())
  }

  return {
    ...toRefs(state),
    resetStore, // Expose the reset function
  }
})