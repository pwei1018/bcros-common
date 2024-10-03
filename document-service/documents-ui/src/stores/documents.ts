import type { DocumentInfoIF, DocumentStateIF } from '~/interfaces/document-types-interface'

export const useBcrosDocuments = defineStore('bcros/documents', () => {

  // Function to return default values
  const getDefaultState = (): DocumentStateIF => ({
    // Document Search
    searchResultCount: 0,
    searchDocumentId: '',
    searchDocuments: '',
    searchEntityId: '',
    searchEntityType: '',
    searchDocumentClass: '',
    searchDocumentType: '',
    searchDateRange: { start: null, end: null },
    searchDescription: '',
    pageNumber: 1,

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
    documentListSnapshot: [],
    scanningDetails: null,
    scanningDetailsSnapshot: null,

    // Validations
    validateIndex: false,
    validateRecordEdit: false,
    isLoading: false,
    validateDocumentSearch: false,

    // Document Review
    displayDocumentReview: false,
    documentInfoRO: null as DocumentInfoIF,
    documentSearchResults: [],
    documentRecord: null,
    documentRecordSnapshot: null,

    // Document Editing
    isEditing: false,
    isEditingReview: false,
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