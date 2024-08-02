export interface DocumentDetailIF {
  type: string
  description: string
  productCode: string
}

export interface DocumentClassIF {
  class: string
  prefixes: Array<string>
  documents: Array<DocumentDetailIF>
}

export interface DocumentTypesIF {
  [key: string]: DocumentClassIF
}