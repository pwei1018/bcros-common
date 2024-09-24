import { useBcrosDocuments } from '~/stores/documents'
import { getDocuments, postDocument } from '~/utils/documentRequests'
import type { ApiResponseIF, ApiResponseOrError, DocumentRequestIF } from '~/interfaces/request-interfaces'
import type { DocumentDetailIF, DocumentInfoIF } from '~/interfaces/document-types-interface'
import { formatIsoToYYYYMMDD } from '~/utils/dateHelper'

export const useDocuments = () => {
  const {
    consumerDocumentId,
    noDocIdCheckbox,
    consumerIdentifier,
    noIdCheckbox,
    description,
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
  function getDocumentTypesByClass(documentClass: string = undefined): Array<DocumentDetailIF>|[]  {
    return documentClass 
    ? documentTypes.find(doc => doc.class === documentClass)?.documents || []
    : documentTypes.reduce((docTypes: Array<DocumentDetailIF>, currentValue) => {
      docTypes.push(...currentValue.documents); // Assuming currentValue.documents is an array
      return docTypes;
    }, [])
  }

  /**
   * Retrieves the description based on the provided class or type value.
   *
   * @param value - The class or type value to look up.
   * @param isType - Boolean indicating whether the value is a type or class. Defaults to false (class).
   * @returns The description of the class or type if found, otherwise undefined.
   */
  function getDocumentDescription(value: string, isType = false): string | undefined {
    const docClass = documentTypes.find(docClass =>
      isType
        ? docClass.documents.some(doc => doc.type === value)
        : docClass.class === value
    )

    return isType
      ? docClass?.documents.find(doc => doc.type === value)?.description
      : docClass?.description
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
  const searchDocumentRecords = async (): Promise<void> => {
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
    return (!!consumerIdentifier.value || !!noIdCheckbox.value)
      && (!!consumerDocumentId.value || !!noDocIdCheckbox.value)
      && !!documentClass.value
      && !!documentType.value
      && !!consumerFilingDate.value
      && description.value.length <= 1000
  })

  const debouncedSearch = debounce(searchDocumentRecords)

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
              description: description.value,
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

  /** Scroll to the first error element on the page */
  const scrollToFirstError = () => {
    // Find the first element with the class "placeholder:text-red-500"
    const errorElement = document.querySelector('.placeholder\\:text-red-500');

    // If found, scroll to it
    if (errorElement) {
      errorElement.scrollIntoView({ behavior: 'smooth' });
    } else {
      console.warn('No error found.');
    }
  }

  watch(() => searchEntityId.value, (id: string) => {
    // Format Entity Identifier
    searchEntityId.value = id.replace(/\s+/g, '')?.toUpperCase()
    // Assign and populate a prefix if a match is found
    if (id.length >= 1) findCategoryByPrefix(id, true)
  })

  return {
    isValidIndexData,
    findCategoryByPrefix,
    getDocumentTypesByClass,
    getDocumentDescription,
    searchDocumentRecords,
    downloadFileFromUrl,
    hasMinimumSearchCriteria,
    saveDocuments,
    debouncedSearch,
    scrollToFirstError
  }
}
