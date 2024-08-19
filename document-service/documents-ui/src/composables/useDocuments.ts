import { useBcrosDocuments } from '~/stores/documents'
import { getDocuments, postDocument } from '~/utils/documentRequests'
import type { ApiResponseIF, ApiResponseOrError, DocumentRequestIF } from '~/interfaces/request-interfaces'
import type { DocumentDetailIF, DocumentInfoIF } from '~/interfaces/document-types-interface'
import { formatIsoToYYYYMMDD } from '~/utils/dateHelper'

export const useDocuments = () => {
  const {
    consumerIdentifier,
    documentClass,
    documentType,
    consumerFilingDate,
    documentList,
    validateIndex,
    isLoading,
    documentInfoRO,
    displayDocumentReview,
    searchDocumentId,
    searchEntityId,
    searchDocumentClass,
    searchDocumentType,
    validateDocumentSearch,
    documentSearchResults,
    searchDateRange
  } = storeToRefs(useBcrosDocuments())

  /**
   * Retrieves document descriptions for the specified category
   * @param documentClass - The document class for which to retrieve documents
   * @returns An array of document descriptions or an empty array if the category is not found
   */
  function getDocumentTypesByClass(documentClass: string): Array<DocumentDetailIF>|[]  {
    return documentTypes.find(doc => doc.class === documentClass)?.documents || []
  }

  /**
   * Retrieves class descriptions for the specified category
   * @param documentClass - The document class for which to retrieve documents
   * @returns An class descriptions or an empty string if the category is not found
   */
  function getDocumentClassDescription(documentClass: string): string  {
    return documentTypes.find(doc => doc.class === documentClass)?.description || ''
  }

  /**
   * Finds the category based on the prefix of the entity identifier.
   * @param identifier - The entity identifier to search.
   * @param isSearch - Flag to determine if the search is for the search form.
   * @returns The category associated with the prefix or null if no match is found.
   */
  function findCategoryByPrefix(identifier: string, isSearch: boolean = false): void {
    const match = identifier.match(/^([A-Za-z]+)\d*/)
    const prefix = match ? match[1].toUpperCase() : '' // Extract prefix

    for (const documentType of documentTypes) {
      if (documentType.prefixes.includes(prefix)) {
        !isSearch
          ? documentClass.value = documentType.class
          : searchDocumentClass.value = documentType.class
        return
      }
    }
  }

  /** Computed flag to check if there are no search criteria **/
  const hasMinimumSearchCriteria = computed(() => {
    return searchDocumentClass.value && (searchDocumentId.value || searchEntityId.value)
  })

  /**
   * Removes duplicate documents based on consumerDocumentId and aggregates filenames.
   * @param {Array} docs - Array of document objects with consumerDocumentId and consumerFilename.
   * @returns {Array} Array of unique documents with aggregated filenames.
   */
  function consolidateDocIds(docs: Array<DocumentRequestIF>) {
    const map = new Map()

    docs.forEach(doc => {
      const { consumerDocumentId, consumerFilename, documentURL, ...rest } = doc

      if (!map.has(consumerDocumentId)) {
        map.set(consumerDocumentId, {
          consumerDocumentId,
          consumerFilenames: [consumerFilename],
          documentUrls: [documentURL],
          ...rest
        })
      } else {
        const existingDoc = map.get(consumerDocumentId)
        if (consumerFilename) {
          existingDoc.consumerFilenames.push(consumerFilename)
        }
        if (documentURL) {
          existingDoc.documentUrls.push(documentURL)
        }
      }
    })

    return Array.from(map.values())
  }

  /** Validate and Search Documents **/
  const searchDocuments = async (): Promise<void> => {
    validateDocumentSearch.value = true

    if (hasMinimumSearchCriteria.value) {
      try {
        isLoading.value = true
        const response: ApiResponseIF = await getDocuments(
          {
            consumerDocumentId: searchDocumentId.value,
            consumerIdentifier: searchEntityId.value,
            documentClass: searchDocumentClass.value,
            documentType: searchDocumentType.value,
            ...(searchDateRange.value?.end && {
              queryStartDate: formatIsoToYYYYMMDD(searchDateRange.value.start),
              queryEndDate: formatIsoToYYYYMMDD(searchDateRange.value.end)
            })
          }
        ) as ApiResponseIF
        isLoading.value = false
        documentSearchResults.value = consolidateDocIds(response.data.value)
      }
      catch (error) {
        console.error('Request failed:', error)
      }
    }
  }

  /**
   * Downloads a file from the given URL.
   *
   * @param {string} url - The URL of the file to download.
   * @param {string} filename - The name to save the file as.
   */
  function downloadFileFromUrl(url: string, filename: string): void {
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.target = '_blank' // This opens the link in a new browser tab

    // Append to the document and trigger the download
    document.body.appendChild(link)
    link.click()

    // Remove the link after the download is triggered
    document.body.removeChild(link)
  }

  /** Computed validation flag to check for required document meta data **/
  const isValidIndexData = computed(() => {
    return !!consumerIdentifier.value
      && !!documentClass.value
      && !!documentType.value
      && !!consumerFilingDate.value
  })

  /** Validate and Save Document Indexing */
  const saveDocuments = async (): Promise<void> => {
    // Validate Document Indexing
    validateIndex.value = true

    if (isValidIndexData.value) {
      isLoading.value = true

      // Initialize an object to hold the consolidated data
      const consolidatedResponse = {
        data: null as DocumentInfoIF,
        fileNames: [] as string[],
        consumerDocumentId: '', // To store the consumerDocumentID from the first request
      }

      try {
        // Iterate over the document list and handle requests sequentially
        for (const document of documentList.value) {
          const response: ApiResponseOrError = await postDocument(
            {
              consumerIdentifier: consumerIdentifier.value,
              documentClass: documentClass.value,
              documentType: documentType.value,
              consumerFilingDate: formatDateToISO(consumerFilingDate.value),
              consumerFilename: document.name,
              // If a consumerDocumentId is needed for subsequent requests, it can be added here
              ...(consolidatedResponse.consumerDocumentId && {
                consumerDocumentId: consolidatedResponse.consumerDocumentId
              })
            },
            document
          )

          if ('data' in response) {
            // Store the data only once (assuming all successful responses have identical data)
            if (!consolidatedResponse.data) {
              consolidatedResponse.data = response.data.value
              // Store the consumerDocumentId from the first request
              consolidatedResponse.consumerDocumentId = response.data.value.consumerDocumentId
            }

            // Add the document name to the fileNames array
            consolidatedResponse.fileNames.push(document.name)

          } else {
            console.warn('Error:', response.message, response.status, response.statusText)
            isLoading.value = false
            return // Exit if there is an error in any request
          }
        }

        // Store the consolidated result after all requests have completed
        documentInfoRO.value = { ...consolidatedResponse.data, filenames: consolidatedResponse.fileNames }

        // Display the document review
        isLoading.value = false
        displayDocumentReview.value = true
      } catch (error) {
        console.error('Request failed:', error)
        isLoading.value = false
      }
    }
  }

  return {
    isValidIndexData,
    findCategoryByPrefix,
    getDocumentTypesByClass,
    getDocumentClassDescription,
    searchDocuments,
    downloadFileFromUrl,
    hasMinimumSearchCriteria,
    saveDocuments
  }
}
