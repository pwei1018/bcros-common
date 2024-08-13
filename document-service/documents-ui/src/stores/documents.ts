import type { DocumentInfoIF } from '~/interfaces/document-types-interface'

export const useBcrosDocuments = defineStore('documents', () => {
  // Document Meta
  const consumerIdentifier = ref('')
  const noIdCheckbox = ref(false)
  const documentClass = ref('')
  const documentType = ref('')
  const consumerFilingDate = ref('')

  // Documents
  const documentList = ref([])

  // Validations
  const validateIndex = ref()
  const isLoading = ref(false)

  // Review
  const displayDocumentReview = ref(false)
  const documentInfoRO = ref(null as DocumentInfoIF)

  return {
    consumerIdentifier,
    noIdCheckbox,
    documentClass,
    documentType,
    consumerFilingDate,
    documentList,
    validateIndex,
    isLoading,
    displayDocumentReview,
    documentInfoRO
  }
})