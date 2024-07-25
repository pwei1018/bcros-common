import type { AccountTypeE } from '@/enums/account-type-e'
import type { AccountStatusE } from '@/enums/account-status-e'
import type { UserSettingsTypeE } from '@/enums/user-settings-type-e'

export interface AccountI {
  id: number
  accountType: AccountTypeE
  accountStatus: AccountStatusE
  additionalLabel?: string
  label: string
  type: UserSettingsTypeE.ACCOUNT
  urlpath: string
  urlorigin: string
}
