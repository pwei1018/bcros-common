import type { DocumentInfoIF } from '~/interfaces/document-types-interface'

export const useBcrosDocuments = defineStore('bcros/documents', () => {

  // Function to return default values
  const getDefaultState = () => ({
    // Document Search
    searchDocumentId: '',
    searchEntityId: '',
    searchDocumentClass: '',
    searchDocumentType: '',
    searchDateRange: { start: null, end: null },

    // Document Meta
    consumerIdentifier: '',
    noIdCheckbox: false,
    documentClass: '',
    documentType: '',
    consumerFilingDate: '',
    documentList: [],

    // Validations
    validateIndex: undefined,
    isLoading: false,
    validateDocumentSearch: false,

    // Document Review
    displayDocumentReview: false,
    documentInfoRO: null as DocumentInfoIF,
    documentSearchResults: [],
  })

  // Initial state
  const state = reactive(getDefaultState())

  // Reset function
  const resetStore = () => {
    Object.assign(state, getDefaultState())
  }

  return {
    ...toRefs(state),
    resetStore, // Expose the reset function
  }
})