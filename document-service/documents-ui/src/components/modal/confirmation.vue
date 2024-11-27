<script setup lang="ts">
defineProps({
  toggleModal: {
    type: Boolean,
    default: false
  }
})
const emit = defineEmits(['close', 'confirm'])
</script>

<template>
  <UModal :model-value="toggleModal" :data-cy="'confirmation-modal'" prevent-close>
    <div class="p-10">
      <div class="flex justify-between items-center">
        <h3 class="text-[24px] font-bold items-center">{{ $t('cancelDialog.title') }}</h3>
        <UButton
          icon="i-mdi-close"
          size="md"
          color="primary"
          variant="ghost"
          :padded="false"
          @click="emit('close')"
        />
      </div>

      <div class="pr-4">

        <div class="flex flex-row py-6">
          <span class="text-gray-700 font-normal text-base leading-6">{{ $t('cancelDialog.description') }}</span>
        </div>

        <div class="grid grid-cols-4">
          <div class="col-span-1"/>
          <div class="col-span-2 gap-3 mt-10 flex">
            <UButton
              block
              color="primary"
              class="h-[40px] w-[150px]"
              variant="outline"
              @click="emit('close')"
            >
              {{ $t('cancelDialog.cancelButton') }}
            </UButton>

            <UButton
              block
              color="primary"
              class="h-[40px] w-[150px]"
              @click="emit('confirm')"
            >
              {{ $t('cancelDialog.confirmButton') }}
            </UButton>
          </div>
          <div class="col-span-1"/>
        </div>
      </div>
    </div>
  </UModal>
</template>