import type { AxiosError } from 'axios'
import type {
  ApiResponseOrError,
  RequestDataIF
} from '~/interfaces/request-interfaces'
import { SessionStorageKeys } from `~/enums/sessionStorageKeys`

/**
 * Converts a document to PDF by sending a POST request to the PDF conversion API.
 *
 * @param document - The document data to be converted, conforming to RequestDataIF.
 * @returns A promise that resolves to a PDF blob on success, or an error object with message, status, and statusText on failure.
 */
export async function pdfConversion(document: RequestDataIF)
  : Promise<ApiResponseOrError> {
  const config = useRuntimeConfig()
  const baseURL = config.public.documentsApiURL
  const docApiKey = config.public.documentsApiKey
  const authorization = `Bearer ${sessionStorage.getItem(SessionStorageKeys.KeyCloakToken)}`
  const currentAccount = sessionStorage.getItem(SessionStorageKeys.CurrentAccount)


  const options = {
    method: 'POST',
    headers: {
      'Accept': 'application/pdf',
      'x-apikey': `${docApiKey}`,
      'Account-Id': JSON.parse(currentAccount)?.id,
      authorization
    },
    body: document
  }

  const url = `${baseURL}/pdf-conversions`
  try {
    const response = await $fetch(url, options)
    if (!(response instanceof Blob)) {
      throw { message: 'No PDF blob returned', status: 'error' }
    }
    return response
  } catch (error) {
    return {
      message: (error as Error).message,
      status: (error as AxiosError)?.response?.status || 'error',
      statusText: 'Error occurred while converting document to PDF'
    }
  }
}
