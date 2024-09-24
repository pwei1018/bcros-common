import type { DocumentInfoIF, DocumentStateIF } from '~/interfaces/document-types-interface'

export const useBcrosDocuments = defineStore('bcros/documents', () => {

  // Function to return default values
  const getDefaultState = (): DocumentStateIF => ({
    // Document Search
    searchDocumentId: '',
    searchDocuments: '',
    // Pre-populated these values for review purpose.
    searchEntityId: 'NR123',
    searchDocumentClass: 'NR',
    searchDocumentType: 'NR_MISC',
    searchDateRange: { start: null, end: null },

    // Document Meta
    consumerDocumentId: '',
    consumerIdentifier: '',
    noIdCheckbox: false,
    noDocIdCheckbox: false,
    documentClass: '',
    documentType: '',
    description: '',
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
    documentRecord: null,

    // Document Editing
    isEditing: false
  })

  // Initial state
  const state = reactive(getDefaultState())

  // Reset state function
  const resetStore = () => {
    Object.assign(state, getDefaultState())
  }

  return {
    ...toRefs(state),
    resetStore
  }
})