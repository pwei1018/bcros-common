import { useBcrosDocuments } from "~/stores/documents"
import { getDocuments } from "~/utils/documentRequests"
import type {
  ApiResponseIF,
  DocumentRequestIF,
} from "~/interfaces/request-interfaces"
import type { DocumentDetailIF } from "~/interfaces/document-types-interface"
import { formatIsoToYYYYMMDD } from "~/utils/dateHelper"

export const useDocumentSearch = () => {
  const {
    isLoading,
    searchResultCount,
    searchDocumentId,
    searchEntityId,
    searchDocument,
    searchDocumentClass,
    searchDocumentType,
    documentSearchResults,
    searchDateRange,
    searchDescription,
    pageNumber,
    sortBy,
  } = storeToRefs(useBcrosDocuments())

  /**
   * Retrieves document descriptions for the specified category
   * @param documentClass - The document class for which to retrieve documents
   * @returns An array of document descriptions or an empty array if the category is not found
   */
  function getDocumentTypesByClass(
    documentClass: string = undefined
  ): Array<DocumentDetailIF> | [] {
    return documentClass
      ? documentTypes.find((doc) => doc.class === documentClass)?.documents ||
          []
      : documentTypes.reduce(
          (docTypes: Array<DocumentDetailIF>, currentValue) => {
            docTypes.push(...currentValue.documents) // Assuming currentValue.documents is an array
            return docTypes
          },
          []
        )
  }

  /**
   * Retrieves the description based on the provided class or type value.
   *
   * @param value - The class or type value to look up.
   * @param isType - Boolean indicating whether the value is a type or class. Defaults to false (class).
   * @returns The description of the class or type if found, otherwise undefined.
   */
  function getDocumentDescription(
    value: string,
    isType = false
  ): string | undefined {
    const docClass = documentTypes.find((docClass) =>
      isType
        ? docClass.documents.some((doc) => doc.type === value)
        : docClass.class === value
    )

    return isType
      ? docClass?.documents.find((doc) => doc.type === value)?.description
      : docClass?.description
  }

  /** Computed flag to check if there are no search criteria **/
  const hasMinimumSearchCriteria = computed(() => {
    return (
      searchDocumentClass.value &&
      (searchDocumentId.value || searchEntityId.value)
    )
  })

  /**
   * Removes duplicate documents based on consumerDocumentId and aggregates filenames.
   * @param {Array} docs - Array of document objects with consumerDocumentId and consumerFilename.
   * @returns {Array} Array of unique documents with aggregated filenames.
   */
  function consolidateDocIds(docs: Array<DocumentRequestIF>) {
    const map = new Map()

    docs.forEach((doc) => {
      const { consumerDocumentId, consumerFilename, documentURL, ...rest } = doc

      if (!map.has(consumerDocumentId)) {
        map.set(consumerDocumentId, {
          consumerDocumentId,
          consumerFilenames: [consumerFilename],
          // TODO: Remove Remove google.com once document URL is coming
          documentUrls: documentURL ? [documentURL] : ["https://google.com"],
          ...rest,
        })
      } else {
        const existingDoc = map.get(consumerDocumentId)
        if (consumerFilename) {
          existingDoc.consumerFilenames.push(consumerFilename)
        }
        if (documentURL) {
          existingDoc.documentUrls.push(documentURL)
        } else {
          // TODO: Remove Remove google.com once document URL is coming
          existingDoc.documentUrls.push("https://google.com")
        }
      }
    })

    return Array.from(map.values()) as Array<DocumentRequestIF>
  }

  /** Validate and Search Documents **/
  const searchDocumentRecords = async (): Promise<void> => {
    try {
      isLoading.value = true
      const response: ApiResponseIF = (await getDocuments({
        consumerDocumentId: searchDocumentId.value,
        consumerIdentifier: searchEntityId.value,
        consumerFilename: searchDocument.value,
        documentClass: searchDocumentClass.value,
        documentType: searchDocumentType.value,
        queryStartDate: searchDateRange.value.start,
        queryEndDate: searchDateRange.value.end,
        pageNumber: pageNumber.value > 1 && pageNumber.value,
        ...(searchDateRange.value?.end && {
          queryStartDate: formatIsoToYYYYMMDD(searchDateRange.value.start),
          queryEndDate: formatIsoToYYYYMMDD(searchDateRange.value.end),
        }),
      })) as ApiResponseIF
      isLoading.value = false
      searchResultCount.value = response.data.value.resultCount
      // If the search result is 1st page.
      if (pageNumber.value === 1) {
        documentSearchResults.value = consolidateDocIds(
          response.data.value.results
        )
      } else {
        documentSearchResults.value = [
          ...documentSearchResults.value,
          ...consolidateDocIds(response.data.value.results),
        ]
      }
    } catch (error) {
      console.error("Request failed:", error)
    }
  }

  /**
   * Downloads a file from the given URL.
   *
   * @param {string} url - The URL of the file to download.
   * @param {string} filename - The name to save the file as.
   */
  function downloadFileFromUrl(url: string, filename: string): void {
    const link = document.createElement("a")
    link.href = url
    link.download = filename
    link.target = "_blank" // This opens the link in a new browser tab

    // Append to the document and trigger the download
    document.body.appendChild(link)
    link.click()

    // Remove the link after the download is triggered
    document.body.removeChild(link)
  }

  /** Computed value that checks if search result has next page */
  const hasMorePages = computed(() => {
    return Math.ceil(searchResultCount.value / pageSize) > pageNumber.value
  })

  /** Scroll to the first error element on the page */
  const scrollToFirstError = () => {
    // Find the first element with the class "placeholder:text-red-500"
    const errorElement = document.querySelector(".placeholder\\:text-red-500")

    // If found, scroll to it
    if (errorElement) {
      errorElement.scrollIntoView({ behavior: "smooth" })
    } else {
      console.warn("No error found.")
    }
  }

  /** Get next page of document records if exists */
  const getNextDocumentsPage = async () => {
    if (hasMorePages.value) {
      pageNumber.value += 1
      await searchDocumentRecords().then(()=> sortSearchTable())
    }
  }

  /** Sort document search result by column and direction */
  const sortSearchTable = () => {
    isLoading.value = true

    if (sortBy.value.column === null) {
      isLoading.value = false
      return
    }
    documentSearchResults.value = documentSearchResults.value.sort((a, b) => {
      const aValue = a[sortBy.value.column] ?? null // Treat undefined as null
      const bValue = b[sortBy.value.column] ?? null

      if (aValue === null && bValue === null) return 0 // Both null
      if (aValue === null) return sortBy.value.ascending ? -1 : 1 // a is null, b is not
      if (bValue === null) return sortBy.value.ascending ? 1 : -1 // b is null, a is not

      const comparison = aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      return sortBy.value.ascending ? comparison : -comparison
    })
    isLoading.value = false
  }

  /** Clear filers on Document Records table */
  const clearFilter = () => {
    searchResultCount.value = 0
    searchDocumentId.value = ''
    searchDocument.value = ''
    searchEntityId.value = ''
    searchDocumentClass.value = ''
    searchDocumentType.value = ''
    searchDateRange.value = { start: null, end: null }
    searchDescription.value = ''
    pageNumber.value = 1
  }

  return {
    getDocumentTypesByClass,
    getDocumentDescription,
    searchDocumentRecords,
    downloadFileFromUrl,
    hasMinimumSearchCriteria,
    scrollToFirstError,
    getNextDocumentsPage,
    sortSearchTable,
    clearFilter
  }
}
