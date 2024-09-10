<script setup lang="ts">
import EditRecord from '~/components/documentRecord/EditRecord.vue'
const { isEditing } = storeToRefs(useBcrosDocuments())
const showNavActions = ref(false)

onUnmounted(() => {
  // Toggle Editing
  isEditing.value = false
})
</script>
<template>
  <div
    data-cy="document-records"
    class="grid grid-cols-8 gap-4 mt-12 mb-16"
  >
    <div class="col-span-6">
      <BcrosSection name="documentRecords">
        <template #default>
          <DocumentRecord v-if="!isEditing" @open-edit="isEditing = true" />
          <EditRecord v-else />
        </template>
      </BcrosSection>
    </div>

    <div class="col-span-2 pl-6">
      <NavActionsAside
        v-if="showNavActions"
        :validation-error="false"
        @cancel="navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })"
        @submit="null"
      />
    </div>
  </div>
</template>