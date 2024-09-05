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
    textarea: {
      base: 'text-gray-900 border-0 border-b-[1px] border-gray-500 ring-0 focus:ring-0 h-[125px]',
      placeholder: 'placeholder-gray-700',
      rounded: 'rounded-none rounded-t-md',
      color: {
        gray: {
          outline: 'bg-gray-100 ring-0 hover:bg-gray-200 hover:border-gray-600 ' +
            'focus:border-primary-500 focus:border-b-2 focus:ring-0'
        },
        primary: {
          outline: 'bg-primary-50 ring-0 border-primary-500 hover:bg-gray-200 focus:border-b-2 focus:ring-0'
        },
        red: {
          outline: 'bg-gray-100 ring-0 border-red-600 hover:bg-gray-200 ' +
            'focus:border-red-600 focus:border-b-2 focus:ring-0'
        }
      },
      icon: {
        base: 'text-gray-700',
        color: 'text-{color}-500',
        trailing: {
          padding: {
            sm: 'px-0 pr-2.5',
            md: 'px-0 pr-2.5',
            lg: 'px-0 pr-2.5',
            xl: 'px-0 pr-2.5'
          }
        }
      },
      trailing: {
        padding: {
          sm: 'pe-7',
          md: 'pe-7',
          lg: 'pe-7',
          xl: 'pe-7'
        }
      },
      default: {
        size: 'xl',
        color: 'gray',
        variant: 'outline'
      }
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
    divider: {
      border: {
        base: 'border-gray-500',
        vertical: 'border-red-500'
      },
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
        base: 'min-w-[160px] text-left text-gray-700 font-bold whitespace-nowrap',
      },
      td: {
        base: 'align-top h-[65px] last:block whitespace-normal',
        color: 'text-gray-700',
      }
    }
  }
})