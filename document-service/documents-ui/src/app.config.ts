// Extends app.config.ts from https://github.com/bcgov/business-dashboard-ui/blob/main/src/app.config.ts
// Default Nuxt/UI layer configuration
// └── Extended layer's app.configs override/extend default configs
//     └── This app.config further customizes/extends the extended layer's configurations
export default defineAppConfig({
  ui: {
    formGroup: {
      label: {
        base: 'text-gray-900 text-base font-bold',
        required: "text-red-600",
      },
      disabled: 'text-red-600',
      description: 'text-gray-700 mt-1',
      help: 'text-gray-700 text-xs pl-[15px]',
      error: 'pl-[15px] text-xs',
    },
    input: {
      base: 'relative text-gray-900 border-0 border-b-[1px] border-gray-500 ring-0 focus:ring-0 ' +
        'disabled:cursor-not-allowed disabled:opacity-45'
    },
    select: {
      base: 'bg-white border-b-[1px] border-gray-500 ring-0 focus:border-b-2 focus:ring-0 disabled:cursor-not-allowed' +
        ' disabled:opacity-45',
    },
    checkbox: {
      base: 'h-4 w-4 cursor-pointer border-gray-500',
      border: 'border border-gray-900 dark:border-gray-900',
      label: 'cursor-pointer',
    },
    selectMenu: {
      option: {
        base: 'cursor-pointer',
      },
    },
    modal: {
      overlay: {
        background: 'bg-gray-900/75',
      }
    },
    table: {
      wrapper: 'max-h-[500px] overflow-y-auto',
      th: {
        base: 'w-[200px] text-left text-gray-700 font-bold',
      },
      td: {
        base: 'w-[200px] h-[65px] last:block last:whitespace-normal',
        color: 'text-gray-700',
      }
    }
  }
})