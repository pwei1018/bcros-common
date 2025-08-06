export interface FileHandlerOptionsIF {
  maxFileSize?: number
  minDimensions?: { width: number; height: number }
  maxDimensions?: { width: number; height: number }
  acceptedFileTypes?: string[]
  onConverted?: (files: any[]) => void
}
