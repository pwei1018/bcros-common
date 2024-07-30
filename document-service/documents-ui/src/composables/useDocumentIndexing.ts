export const useDocumentIndexing = () => {
  // Use ref for individual properties
  const entityId = ref('')
  const noIdCheckbox = ref(false)
  const documentCategory = ref('')
  const documentType = ref('')
  const filingDate = ref('')

  // Return the refs and any computed values or methods
  return {
    entityId,
    noIdCheckbox,
    documentCategory,
    documentType,
    filingDate
  }
}
