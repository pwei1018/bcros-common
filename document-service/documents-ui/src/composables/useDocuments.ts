import { useBcrosDocuments } from '~/stores/documents'
import {
  getDocuments,
  postDocument,
  getScanningRecord,
  updateDocumentRecord,
  createScanningRecord,
  updateScanningRecord,
  updateDocument,
  getDocumentUrl
} from '~/utils/documentRequests'
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
    documentRecord,
    documentRecordSnapshot,
    scanningDetails,
    scanningDetailsSnapshot,
    documentList,
    documentListSnapshot,
    validateIndex,
    isLoading,
    documentInfoRO,
    displayDocumentReview,
    searchResultCount,
    searchDocumentId,
    searchEntityId,
    searchDocumentClass,
    searchDocumentType,
    documentSearchResults,
    searchDateRange,
    pageNumber
  } = storeToRefs(useBcrosDocuments())

  /** Computed flag to check if there are any changes in the document metadata **/
  const hasDocumentMetaChanges = computed(() =>
    JSON.stringify(documentRecord.value) !== JSON.stringify(documentRecordSnapshot.value)
  )

  /** Computed flag to check if there are any changes in the document scanning record **/
  const hasDocumentScanningChanges = computed(() =>
    JSON.stringify(scanningDetails.value) !== JSON.stringify(scanningDetailsSnapshot.value)
  )

  /** Computed flag to check if there are any changes to the document files **/
  const hasDocumentFileChanges = computed(() => {
    return documentListSnapshot.value.length !== documentList.value.length ||
      documentListSnapshot.value.some((file, index) =>
        file.name !== documentList.value[index].name)
  })

  /** Computed flag to check if there are any changes in the document record **/
  const hasDocumentRecordChanges = computed(() => {
    return hasDocumentMetaChanges.value || hasDocumentScanningChanges.value || hasDocumentFileChanges.value

  })

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
          // TODO: Remove Remove google.com once document URL is coming
          documentUrls: documentURL ? [documentURL] : ["https://google.com"],
          ...rest
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
          existingDoc.documentUrls.push("https://google.com");
        }
      }
    })

    return Array.from(map.values()) as Array<DocumentRequestIF>;
  }

  /** Validate and Search Documents **/
  const searchDocumentRecords = async (): Promise<void> => {
    try {
      isLoading.value = true
      const response: ApiResponseIF = (await getDocuments({
        pageNumber: pageNumber.value,
        consumerDocumentId: searchDocumentId.value,
        consumerIdentifier: searchEntityId.value,
        documentClass: searchDocumentClass.value,
        documentType: searchDocumentType.value,
        ...(searchDateRange.value?.end && {
          queryStartDate: formatIsoToYYYYMMDD(searchDateRange.value.start),
          queryEndDate: formatIsoToYYYYMMDD(searchDateRange.value.end),
        }),
      })) as ApiResponseIF;
      isLoading.value = false;
      searchResultCount.value = response.data.value.resultCount;
      documentSearchResults.value = [
        ...documentSearchResults.value,
        ...consolidateDocIds(response.data.value.results)
      ]
    } catch (error) {
      console.error("Request failed:", error);
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

  /**
   * Downloads a document from the given document service ID.
   *
   * @param {string} documentClass - The class of the document to download.
   * @param {string} docServiceId - The document service ID of the document to download.
   */
  const fetchUrlAndDownload = async (documentClass: string, docServiceId: string): void => {
    const { data } = await getDocumentUrl(documentClass, docServiceId)
    const link = document.createElement('a')
    link.href = data.value[0].documentURL
    link.download = data.value[0].consumerFilename
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

  /** Computed value that checks if search result has next page */
  const hasMorePages = computed(() => {
    return Math.ceil(searchResultCount.value / pageSize) > pageNumber.value
  })

  /** Computed validation flag to check for required document meta data **/
  const isValidRecordEdit = computed(() => {
    return (!!documentRecord.value.consumerIdentifier || !!noIdCheckbox.value)
      && !!documentRecord.value.documentClass
      && !!documentRecord.value.documentType
      && !!documentRecord.value.consumerFilingDateTime
      && description.value.length <= 1000
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
              consumerDocumentId: consumerDocumentId.value,
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

  /** Validate and Update Document Records and Scanning information */
  const updateDocuments = async (): Promise<void> => {
    if (isValidRecordEdit.value) {
      isLoading.value = true

      try {
        // Iterate over the document list and handle requests sequentially
        for (const document of documentList.value) {

          // Update Document Record Meta Data
          if (hasDocumentMetaChanges.value) {
            await updateDocumentRecord({
              documentServiceId: documentRecord.value.documentServiceId,
              consumerDocumentId: documentRecord.value.consumerDocumentId,
              consumerIdentifier: documentRecord.value.consumerIdentifier,
              documentClass: documentRecord.value.documentClass,
              documentType: documentRecord.value.documentType,
              description: documentRecord.value.description,
              consumerFilingDate: formatDateToISO(documentRecord.value.consumerFilingDateTime),
            })
          }

          // Update Document Files
          if (hasDocumentFileChanges.value && !!document.size) {
            await updateDocument({
                documentServiceId: documentRecord.value.documentServiceId,
                consumerFilename: document.name,
              },
              document
            )
          }

          // Update or Create Scanning Details
          if (hasDocumentScanningChanges.value) {
            // Update Scanning Data
            const scanningData = await updateScanningRecord({
              consumerDocumentId: documentRecord.value.consumerDocumentId,
              documentClass: documentRecord.value.documentClass,
              scanningDetails: scanningDetails.value,
            })

            if (scanningData.statusCode === 404) {
              await createScanningRecord({
                consumerDocumentId: documentRecord.value.consumerDocumentId,
                documentClass: documentRecord.value.documentClass,
                scanningDetails: scanningDetails.value,
              })
            }
          }
        }
      } catch (error) {
        console.error('Request failed:', error);
      } finally {
        isLoading.value = false  // Ensure loading is false regardless of success or error
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

  /** Get next page of document records if exists */
  const getNextDocumentsPage = () => {
    if(hasMorePages.value) {
      pageNumber.value += 1
      searchDocumentRecords()
    }
  } 

  /**
   * Async function to retrieve and update document data:
   * - Fetches document record and populates `documentRecord` and `documentList`.
   * - If `accessionNumber` is missing, attempts to fetch and merge scanning data.
   */
  const retrieveDocumentRecord = async (identifier: string) => {
    try {
      // Fetch Document Record
      const { data } = await getDocumentRecord(identifier)
      if (data.value) {
        documentRecord.value = {
          ...data.value[0],
          consumerFilenames: data.value.map((record) => (record.consumerFilename)),
          documentServiceIds: data.value.map((record) => (record.documentServiceId))
        }
        documentList.value = documentRecord.value.consumerFilenames?.map((file) => ({
          name: file
        }))

        // Fetch Scanning Data
        const scanningData = await getScanningRecord(documentRecord.value?.documentClass, identifier)
        scanningDetails.value = { ...scanningData.data.value }

        // Set Snapshots for change tracking
        documentRecordSnapshot.value = { ...documentRecord.value }
        documentListSnapshot.value = [...documentList.value]
        scanningDetailsSnapshot.value = { ...scanningData.data.value }

      }
    } catch (error) {
      console.warn('No record found', error)
      navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
    }
  }

  watch(() => searchEntityId.value, (id: string) => {
    // Format Entity Identifier
    searchEntityId.value = id.replace(/\s+/g, '')?.toUpperCase()
    // Assign and populate a prefix if a match is found
    if (id.length >= 1) findCategoryByPrefix(id, true)
  })

  
  return {
    hasDocumentRecordChanges,
    isValidIndexData,
    isValidRecordEdit,
    findCategoryByPrefix,
    getDocumentTypesByClass,
    getDocumentDescription,
    searchDocumentRecords,
    downloadFileFromUrl,
    hasMinimumSearchCriteria,
    saveDocuments,
    updateDocuments,
    scrollToFirstError,
    getNextDocumentsPage,
    retrieveDocumentRecord,
    fetchUrlAndDownload
  }
}
