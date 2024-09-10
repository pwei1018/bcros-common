<script setup lang="ts">
const emit = defineEmits(['cancel', 'submit'])
</script>
<template>
  <div
    data-cy="nav-footer"
    class="w-full bg-white"
  >
    <div class="app-inner-container h-[100px] content-center">
      <div class="flex flex-row-reverse">
        <UButton
          block
          trailing-icon="i-mdi-chevron-right"
          color="primary"
          class="h-[40px] w-[180px] ml-[10px] font-bold px-3"
          data-cy="nav-footer-save-btn"
          @click="emit('submit')"
        >
          Save and Record
        </UButton>

        <UButton
          block
          color="primary"
          class="h-[40px] w-[100px] px-3"
          variant="outline"
          data-cy="nav-footer-cancel-btn"
          @click="emit('cancel')"
        >
          Cancel
        </UButton>
      </div>
    </div>
  </div>
</template>