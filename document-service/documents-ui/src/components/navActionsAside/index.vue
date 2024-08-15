<script setup lang="ts">
defineProps({
  validationError: { type: Boolean, default: false }
})
const emit = defineEmits(['cancel', 'submit'])
const { documentList } = storeToRefs(useBcrosDocuments())
</script>
<template>
  <aside data-cy="nav-actions-aside">
    <div class="rounded">
      <div class="px-4 py-2 bg-bcGovColor-darkBlue	h-[40px] rounded-t">
        <span class="text-white font-bold">{{ $t('title.documentIndexing') }}</span>
      </div>
      <div class="flex flex-row px-4 py-2 bg-white h-[40px] rounded-b">
        <span class="text-gray-900 font-bold text-sm basis-full">{{ $t('documentUpload.asideDescription') }}</span>
        <span>{{ documentList.length || '-' }}</span>
      </div>
    </div>

    <UButton
      block
      color="primary"
      class="h-[40px] my-3"
      variant="outline"
      @click="emit('cancel')"
    >
      Cancel
    </UButton>

    <UButton
      block
      color="primary"
      class="h-[40px] font-bold"
      @click="emit('submit')"
    >
      Save
    </UButton>

    <div v-if="validationError" class="text-center text-red-500 text-[12px] mt-2">
      <span>{{ $t('documentIndexing.incompleteError') }}</span>
    </div>
  </aside>
</template>