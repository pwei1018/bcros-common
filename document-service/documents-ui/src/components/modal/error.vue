<script setup lang="ts">
import { copyToClipboard } from '~/utils/copyToClipboard';
const {
  isError,
  errorMsg
} = storeToRefs(useBcrosDocuments())
const toast = useToast()
const isErrorExpanded = ref(false)

const copyErrorMsg = () => {
    if(errorMsg.value.length > 0 ) {
        copyToClipboard(JSON.stringify(errorMsg.value))
        toast.add({ title: 'Error content copied to clipboard.' })
    } else {
        toast.add({ title: 'Nothing to copy' })
    }
}

const close = () => {
  isError.value = false
  errorMsg.value = []
}
</script>

<template>
  <UModal :model-value="isError" :data-cy="'error-modal'" prevent-close>
    <div class="p-10">
      <div class="flex justify-between items-center">
        <h3 class="text-[24px] font-bold items-center">{{ $t('errorDialog.title') }}</h3>
        <UButton
          icon="i-mdi-close"
          size="md"
          color="primary"
          variant="ghost"
          :padded="false"
          @click="close"
        />
      </div>

      <div class="pr-4">

        <div class="flex flex-row pt-6">
          <span class="text-gray-700 font-normal text-base leading-6">{{ $t('errorDialog.description') }}</span>
        </div>
        <div>
            <ULink
              class="text-primary underline"
              @click="isErrorExpanded = !isErrorExpanded"
            >
              {{
                isErrorExpanded
                  ? "Hide Error Details"
                  : "View Error Details"
              }}
            </ULink>
        </div>
        <div v-if="isErrorExpanded">
            <div v-for="(err, index) in errorMsg" :key="index">
                {{ err }}
            </div>
        </div>
        <div class="mt-2.5">
            <ULink 
                class="text-primary flex items-end gap-1"
                @click="copyErrorMsg"
            >
                <UIcon name="i-mdi-content-copy" class="w-5 h-5 cursor-pointer" />
                Copy Error Details
            </ULink>
            
        </div>

          <div class="flex mt-10 justify-center">
            <UButton
              block
              color="primary"
              class="h-[44px] w-[97px]"
              
              @click="close"
            >
              {{ $t('errorDialog.okButton') }}
            </UButton>
          </div>
        
      </div>
    </div>
  </UModal>
</template>