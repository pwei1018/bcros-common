export const useBcrosDocuments = defineStore('documents', () => {
  // Document Meta
  const consumerIdentifier = ref('')
  const noIdCheckbox = ref(false)
  const documentClass = ref('')
  const documentType = ref('')
  const consumerFilingDate = ref('')

  // Documents
  const documentList = ref([])
  // const consumerFilename = ref(''): Future Payload Property

  // Validations
  const validateIndex = ref()


  return {
    consumerIdentifier,
    noIdCheckbox,
    documentClass,
    documentType,
    consumerFilingDate,
    documentList,
    validateIndex,
  }
})