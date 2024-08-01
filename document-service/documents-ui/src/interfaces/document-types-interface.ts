export interface DocumentDetailIF {
  type: string
  description: string
  productCode: string
}

export interface documentClassIF {
  class: string
  prefixes: Array<string>
  documents: Array<DocumentDetailIF>
}

export interface DocumentTypesIF {
  [key: string]: documentClassIF
}