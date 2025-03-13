import { useBcrosDocuments } from '~/stores/documents'
import {
  postDocument,
  getScanningRecord,
  updateDocumentRecord,
  createScanningRecord,
  updateScanningRecord,
  getDocumentUrl,
  getDocUrlByConsumerDocId,
  putDocument
} from '~/utils/documentRequests'
import type { ApiResponseOrError } from '~/interfaces/request-interfaces'
import type { DocumentDetailIF, DocumentInfoIF } from '~/interfaces/document-types-interface'

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
    uploadedDocumentList,
    validateIndex,
    isLoading,
    documentInfoRO,
    searchDocumentClass
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
    return uploadedDocumentList.value.length > 0
  })

  /** Computed property that combines the document list and uploaded documents. **/
  const updatedDocumentList = computed (() => {
    return [
      ...documentList.value,
      ...uploadedDocumentList.value
    ]
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
    const filteredDocumentTypes = documentClass
    ? documentTypes.find(doc => doc.class === documentClass)?.documents || []
    : documentTypes.reduce((docTypes: Array<DocumentDetailIF>, currentValue) => {
      currentValue.documents.forEach((docType) => {
        if(!docTypes.some((exitingDocType) => exitingDocType.type === docType.type )) {
          docTypes.push(docType)
        }
      })
      return docTypes
    }, [])

    return filteredDocumentTypes.sort((a,b) => a.description.localeCompare(b.description))
  }

  /**
   * Function to get the class description based on the class name.
   * @param className - The class name to search for.
   * @returns The description of the class if found, otherwise an empty string.
   */
  function getClassDescription(className: string): string {
    const documentClass = documentTypes.find(docType => docType.class === className)
    return documentClass ? documentClass.description : ''
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
   * @param {string} docId - The consumer document ID
   * @param {string} docFileName - The consumer document file name
   */
  const fetchUrlAndDownload = async (
    documentClass: string,
    docServiceId = '',
    docId = '',
    docFileName = ''
  ): Promise<void> => {
    const { data } = docServiceId
      ? await getDocumentUrl(documentClass, docServiceId)
      : await getDocUrlByConsumerDocId(documentClass, docId)
    const file = data.value?.find((doc: DocumentRequestIF) => doc.consumerFilename === docFileName) || data.value[0]

    // Create a new link element each time
    const link = document.createElement('a')
    link.href = file.documentURL
    link.download = file.consumerFilename
    link.target = '_blank' // This opens the link in a new browser tab

    // Append to the document and trigger the download
    document.body.appendChild(link)
    link.click()

    // Remove the link after the download is triggered
    document.body.removeChild(link)
  }

  /**
   * Downloads all documents associated with a given document class and document ID.
   *
   * @param {string} documentClass - The class of the documents to download.
   * @param {string} [docId=''] - The consumer document ID.
   */
  const downloadAllDocuments = async (documentClass: string, docId = '') => {
    const { data } = await getDocUrlByConsumerDocId(documentClass, docId)
    const files = data.value
    for (const file of files) {
      if (!file.consumerFilename || !file.documentURL) continue

      // Create a temporary anchor element
      const link = document.createElement('a')
      link.href = file.documentURL
      link.download = file.consumerFilename
      link.target = '_blank' // This opens the link in a new browser tab

      // Append the anchor element to the document body
      document.body.appendChild(link)

      // Programmatically click the anchor element to trigger the download
      link.click()

      // Remove the anchor element from the document body
      document.body.removeChild(link)

      // Focus back on the current window
      window.focus()
    }
  }

  /** Computed validation flag to check for required document meta data **/
  const isValidIndexData = computed(() => {
    return (!!consumerIdentifier.value || !!noIdCheckbox.value)
      && (!!consumerDocumentId.value || !!noDocIdCheckbox.value)
      && !!documentClass.value
      && !!documentType.value
      && description.value.length <= 1000
  })

  /** Computed validation flag to check for required document meta data **/
  const isValidRecordEdit = computed(() => {
    return (!!documentRecord.value.consumerIdentifier || !!noIdCheckbox.value)
      && !!documentRecord.value.documentClass
      && !!documentRecord.value.documentType
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
        for (const document of uploadedDocumentList.value) {
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
      } catch (error) {
        console.error('Request failed:', error)
        isLoading.value = false
      }
    }
  }

  /** Update document record and scanning information */
  const updateDocument = async (document?: File): Promise<void> => {
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
      if(!!documentRecord.value.documentServiceId && !documentRecord.value.consumerFilename) {
        await putDocument(
          {
            consumerFilename: document.name,
            documentServiceId: documentRecord.value.documentServiceId
          },
          document
        )
      } else {
        await postDocument(
          {
            consumerDocumentId: documentRecord.value.consumerDocumentId,
            consumerIdentifier: documentRecord.value.consumerIdentifier,
            documentClass: documentRecord.value.documentClass,
            documentType: documentRecord.value.documentType,
            description: documentRecord.value.description,
            consumerFilingDate: formatDateToISO(documentRecord.value.consumerFilingDateTime),
            consumerFilename: document.name
          },
          document
        )
      }
    }
    // Update or Create Scanning Details
    if (hasDocumentScanningChanges.value) {
      // Update Scanning Data
      const scanningData = await updateScanningRecord({
        consumerDocumentId: documentRecord.value.consumerDocumentId,
        documentClass: documentRecord.value.documentClass,
        scanningDetails: scanningDetails.value,
      }, true)
      if (scanningData.statusCode === 404) {
        await createScanningRecord({
          consumerDocumentId: documentRecord.value.consumerDocumentId,
          documentClass: documentRecord.value.documentClass,
          scanningDetails: scanningDetails.value,
        })
      }
    }
  }

  /** Validate and Update Document Records and Scanning information */
  const updateDocuments = async (): Promise<void> => {
    if (isValidRecordEdit.value) {
      isLoading.value = true

      try {
        // Iterate over the document list and handle requests sequentially
        if(updatedDocumentList.value.length > 0) {
          for (const document of updatedDocumentList.value) {
            await updateDocument(document)
          }
        } else {
          await updateDocument()
        }
      } catch (error) {
        console.error('Request failed:', error)
      } finally {
        isLoading.value = false  // Ensure loading is false regardless of success or error
      }
    }
  }

  /** Scroll to the first error element on the page */
  const scrollToFirstError = () => {
    // Find the first element with the class "placeholder:text-red-500"
    const errorElement = document.querySelector('.placeholder\\:text-red-500')

    // If found, scroll to it
    if (errorElement) {
      errorElement.scrollIntoView({ behavior: 'smooth' })
    } else {
      console.warn('No error found.')
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
      const { data, status } = await getDocumentRecord(identifier)
      if(status.value === 'error') {
        navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
      }
      if (data.value) {
        const consumerFilenames = []
        data.value.forEach(record => (record.consumerFilename && consumerFilenames.push(record.consumerFilename)))
        documentRecord.value = {
          ...data.value.find(record => !!record.consumerFilename) || data.value[0],
          consumerFilenames: consumerFilenames,
          documentServiceIds: data.value.filter(record => record.consumerFilename)
            .map((record) => (record.documentServiceId))
        }
        documentList.value = documentRecord.value.consumerFilenames?.map((file) => ({
          name: file
        }))

        // Fetch Scanning Data
        const scanningData = await getScanningRecord(documentRecord.value?.documentClass, identifier)
        scanningDetails.value = { ...scanningData.data.value }

        // Set Snapshots for change tracking
        documentRecordSnapshot.value = { ...documentRecord.value }
        uploadedDocumentList.value = []
        scanningDetailsSnapshot.value = { ...scanningData.data.value }

      }
    } catch (error) {
      console.warn('No record found', error)
      navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })
    }
  }

  return {
    hasDocumentRecordChanges,
    isValidIndexData,
    isValidRecordEdit,
    updatedDocumentList,
    findCategoryByPrefix,
    getDocumentTypesByClass,
    getClassDescription,
    getDocumentDescription,
    downloadFileFromUrl,
    saveDocuments,
    updateDocuments,
    scrollToFirstError,
    retrieveDocumentRecord,
    fetchUrlAndDownload,
    downloadAllDocuments
  }
}
