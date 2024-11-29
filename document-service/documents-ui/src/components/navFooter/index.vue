<script setup lang="ts">
const { hasDocumentRecordChanges } = useDocuments()
const emit = defineEmits(['cancel', 'back', 'next'])
const props = defineProps({
  cancelBtn: {
    type: String,
    default: ''
  },
  nextBtn: {
    type: String,
    default: ''
  },
  backBtn: {
    type: String,
    default: ''
  }
})
const isNoChangeError = computed(() => {
  return !hasDocumentRecordChanges.value && props.nextBtn === 'Review and Confirm'
})
</script>
<template>
  <div
    data-cy="nav-footer"
    class="w-full bg-white"
  >
    <div class="app-inner-container h-[100px] content-center">
      <div class="grid grid-cols-6 gap-2">

        <div class="col-span-1">
          <UButton
            v-if="props.cancelBtn"
            color="primary"
            class="h-[40px] px-7"
            variant="outline"
            data-cy="nav-footer-cancel-btn"
            @click="emit('cancel')"
          >
            {{ props.cancelBtn }}
          </UButton>
        </div>

        <div class="col-span-3"/>

        <div class="col-span-1">
          <UButton
            v-if="props.backBtn"
            leading-icon="i-mdi-chevron-left"
            color="primary"
            variant="outline"
            class="h-[40px] px-7 float-right"
            data-cy="nav-footer-back-btn"
            @click="emit('back')"
          >
            {{ props.backBtn }}
          </UButton>
        </div>

        <div class="col-span-1 text-center">
         
        <UButton
            v-if="props.nextBtn"
            trailing-icon="i-mdi-chevron-right"
            color="primary"
            class="h-[40px] ml-[10px] font-bold px-5 text-nowrap"
            data-cy="nav-footer-next-btn"
            @click="emit('next')"
          >
            {{ props.nextBtn }}
          </UButton>
          <span
            :class="['text-red-600', 'text-xs', isNoChangeError ? '' : 'invisible']"
          >
            No changes has been made
          </span>
        </div>

      </div>
    </div>
  </div>
</template>