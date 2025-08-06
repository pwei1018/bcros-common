export default defineAppConfig({
  ui: {
    fileUpload: {
      slots: {
        root: 'relative flex flex-col',
        base: [
          'w-full flex-1 bg-default border border-default flex flex-col gap-2 items-stretch justify-center rounded-lg focus-visible:outline-2',
          'transition-[background]'
        ],
        wrapper: 'flex flex-col items-center justify-center text-center',
        icon: 'shrink-0',
        avatar: 'shrink-0',
        label: 'text-base text-default mt-2 text-bcGovGray-700 font-bold',
        description: 'text-bcGovGray-700 my-2 text-base',
        actions: 'flex flex-wrap gap-1.5 shrink-0 mt-4',
        file: 'relative bg-white gap-4 p-6! border-x-0 border-t-0! rounded-[0px]!',
        fileLeadingAvatar: 'shrink-0',
        fileWrapper: 'flex flex-col min-w-0',
        fileName: 'text-default truncate',
        fileSize: 'text-muted truncate',
        fileTrailingButton: ''
      }
    },
    button: {
      slots: {
        base: [
          'cursor-pointer rounded-md font-medium inline-flex items-center disabled:cursor-not-allowed ' +
          'aria-disabled:cursor-not-allowed disabled:opacity-75 aria-disabled:opacity-75',
          'transition-colors'
        ],
        label: 'truncate',
        leadingIcon: 'shrink-0',
        leadingAvatar: 'shrink-0',
        leadingAvatarSize: '',
        trailingIcon: 'shrink-0'
      },
      variants: {
        color: {
          primary: '',
          secondary: '',
          success: '',
          info: '',
          warning: '',
          error: '',
          neutral: ''
        },
        variant: {
          solid: 'px-6! py-2! text-base bg-blue-500! text-white',
          outline: '',
          soft: '',
          subtle: '',
          ghost: 'text-blue-500!',
          link: ''
        }
      },
      compoundVariants: [
        {
          color: 'primary',
          variant: 'ghost',
          class: 'text-primary hover:bg-blue-500/05 active:bg-blue-500/05'
        },
      ],
    },
    progress: {
      variants: {
        color: {
          primary: {
            indicator: 'bg-blue-500!',
            steps: 'text-primary'
          }
        }
      }
    }
  }
})
