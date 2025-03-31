import type { DocumentInfoIF, DocumentStateIF } from '~/interfaces/document-types-interface'

export const useBcrosDocuments = defineStore('bcros/documents', () => {

  // Function to return default values
  const getDefaultState = (): DocumentStateIF => ({
    // Document Search
    searchResultCount: 0,
    searchDocumentId: '',
    searchDocument: '',
    searchEntityId: '',
    searchDocumentClass: '',
    searchDocumentType: '',
    searchDateRange: { start: null, end: null },
    searchDescription: '',
    pageNumber: 1,
    sortBy: { column: null, ascending: true },

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
    // New uploaded document files on edit record.
    uploadedDocumentList: [],
    scanningDetails: null,
    scanningDetailsSnapshot: null,

    // Validations
    validateIndex: false,
    validateRecordEdit: false,
    isLoading: false,
    validateDocumentSearch: false,
    isValidDocId: false,

    // Document Review
    displayDocumentReview: false,
    documentInfoRO: null as DocumentInfoIF,
    documentSearchResults: [],
    documentRecord: null,
    documentRecordSnapshot: null,

    // Document Editing
    isEditing: false,
    isEditingReview: false,

    // Error Handling
    isError: false,
    errorMsg: []
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