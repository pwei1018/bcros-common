import type { ErrorCategoryE } from '~/enums/error-category-e'
import type { ErrorCodeE } from '~/enums/error-code-e'

export interface ErrorI {
  category: ErrorCategoryE,
  detail?: string,
  message: string,
  statusCode: number | null,
  type?: ErrorCodeE
}
