import type { AccountTypeE } from '@/enums/account-type-e'
import type { AccountStatusE } from '@/enums/account-status-e'
import type { UserSettingsTypeE } from '@/enums/user-settings-type-e'

export interface UserSettingsI {
  id: number
  type: UserSettingsTypeE
  urlpath: string
  urlorigin: string
  accountType?: AccountTypeE
  accountStatus?: AccountStatusE
  additionalLabel?: string
  label?: string
}
