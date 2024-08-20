import type { AxiosError } from 'axios'
import type {
  ApiResponseIF,
  ApiResponseOrError,
  DocumentRequestIF,
  RequestDataIF
} from '~/interfaces/request-interfaces'

const config = useRuntimeConfig()
const baseURL = config.public.documentsApiURL
const docApiKey = config.public.documentsApiKey

/**
 * Sends a GET request to fetch a document from the specified API endpoint.
 *
 * @param params - The parameters for the document request, including document class, type, and optional consumer information.
 * @returns A promise that resolves to either an ApiResponseIF on success or an ApiErrorIF on failure.
 */
export async function getDocuments(params: DocumentRequestIF): Promise<ApiResponseOrError> {
  const options = {
    method: 'GET',
    headers: { 'x-apikey': `${docApiKey}` }
  }

  const {
    consumerDocumentId,
    documentClass,
    documentType,
    consumerIdentifier,
    queryStartDate,
    queryEndDate
  } = params

  // Construct query parameters
  const queryParams = new URLSearchParams()
  if (consumerDocumentId) queryParams.append('consumerDocumentId', consumerDocumentId)
  if (consumerIdentifier) queryParams.append('consumerIdentifier', consumerIdentifier)
  if (documentType) queryParams.append('documentType', documentType)
  if (queryStartDate) queryParams.append('queryStartDate', queryStartDate)
  if (queryEndDate) queryParams.append('queryEndDate', queryEndDate)

  // Build the full URL
  const url = `${baseURL}/searches/${documentClass}?${queryParams.toString()}`

  try {
    const response = await useBcrosFetch<ApiResponseIF>(url, options)
    return {
      data: response.data,
      status: response.status
    }
  } catch (error) {
    const axiosError = error as AxiosError
    return {
      message: axiosError.message,
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
    }
  }
}

/**
 * Sends a POST request to upload a document to the specified API endpoint.
 *
 * @param params - The parameters for the document request, including document class, type, and optional consumer
 * information.
 * @param document - The document data to be sent in the request body.
 * @returns A promise that resolves to either an ApiResponseIF on success or an ApiErrorIF on failure.
 */
export async function postDocument(params: DocumentRequestIF, document: RequestDataIF)
  : Promise<ApiResponseOrError> {
  const options = {
    method: 'POST',
    headers: { 'x-apikey': `${docApiKey}` },
    body: document
  }

  const {
    consumerDocumentId,
    documentClass,
    documentType,
    consumerFilename,
    consumerIdentifier,
    consumerFilingDate
  } = params

  // Construct query parameters
  const queryParams = new URLSearchParams()
  if (consumerDocumentId) queryParams.append('consumerDocumentId', consumerDocumentId)
  if (consumerFilename) queryParams.append('consumerFilename', consumerFilename)
  if (consumerIdentifier) queryParams.append('consumerIdentifier', consumerIdentifier)
  if (consumerFilingDate) queryParams.append('consumerFilingDate', consumerFilingDate)

  // Build the full URL
  const url = `${baseURL}/documents/${documentClass}/${documentType}?${queryParams.toString()}`

  try {
    const response = await useBcrosFetch<ApiResponseIF>(url, options)
    return {
      data: response.data,
      status: response.status
    }
  } catch (error) {
    const axiosError = error as AxiosError
    return {
      message: axiosError.message,
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
    }
  }
}

/**
 * Sends a GET request to retrieve a document record by its consumerDocumentId.
 *
 * @param consumerDocumentId - The unique identifier for the document to be retrieved.
 * @returns A promise that resolves to either an ApiResponseIF on success or an ApiErrorIF on failure.
 */
export async function getDocumentRecord(consumerDocumentId: string): Promise<ApiResponseOrError> {
  const options = {
    method: 'GET',
    headers: { 'x-apikey': `${docApiKey}` }
  }

  // Build the full URL
  const url = `${baseURL}/reports/document-records/${consumerDocumentId}`

  try {
    const response = await useBcrosFetch<ApiResponseIF>(url, options)
    saveBlob(response.data.value, `${consumerDocumentId}.pdf`)
    return {
      data: response.data,
      status: response.status
    }
  } catch (error) {
    const axiosError = error as AxiosError
    return {
      message: axiosError.message,
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
    }
  }
}