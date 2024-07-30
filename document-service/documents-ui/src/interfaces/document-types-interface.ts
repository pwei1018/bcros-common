export interface DocumentDetailIF {
  type: string
  description: string
  productCode: string
}

export interface DocumentCategoryIF {
  class: string
  prefixes: Array<string>
  documents: Array<DocumentDetailIF>
}

export interface DocumentTypesIF {
  [key: string]: DocumentCategoryIF
}