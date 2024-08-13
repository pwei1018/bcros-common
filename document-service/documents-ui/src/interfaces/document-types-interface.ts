export interface DocumentDetailIF {
  type: string
  description: string
  productCode: string
}

export interface DocumentClassIF {
  class: string
  description: string
  prefixes: Array<string>
  documents: Array<DocumentDetailIF>
}

export interface DocumentInfoIF {
  consumerDocumentId: string
  consumerFilename: string
  consumerFilingDateTime: string
  consumerIdentifier: string
  createDateTime: string
  documentClass: string
  documentServiceId: string
  documentType: string
  documentTypeDescription: string
  documentURL: string
  filenames: Array<string>
}