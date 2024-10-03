// Define a type for the Axios response data
export interface ApiResponseIF<T = any> {
  data: T
  status: any
  statusText?: string
}

// Define a type for the Axios error response
export interface ApiErrorIF {
  message: string
  status?: number
  statusText?: string
}

export type ApiResponseOrError = ApiResponseIF | ApiErrorIF

// Define a type for the document request parameters
export interface DocumentRequestIF {
  pageNumber?: number
  documentServiceId?: string
  consumerDocumentId?: string
  documentClass: string
  documentType: string
  description?: string
  consumerIdentifier?: string
  consumerFilingDate?: string
  consumerFilename?: string
  productCode?: string
  documentURL?: string
  queryStartDate?: string
  queryEndDate?: string
  description?: string
}

// Define a type for the request data (if any)
export interface RequestDataIF {
  [key: string]: any // Adjust this based on the request payload structure
}