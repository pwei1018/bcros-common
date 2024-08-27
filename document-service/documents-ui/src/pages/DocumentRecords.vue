<script setup lang="ts">
const showNavActions = ref(false)
</script>
<template>
  <div
    data-cy="document-records"
    class="grid grid-cols-8 gap-4 mt-12 mb-16"
  >
    <div class="col-span-6">
      <BcrosSection name="documentRecords">
        <template #header>
          <div class="grid grid-cols-6">
            <div class="col-span-6">
              <h1 class="text-[32px] pb-2">{{ $t('documentRecord.title') }}</h1>
              <span class="text-gray-700 font-normal text-base">{{ $t('documentRecord.description') }}</span>
            </div>
          </div>
        </template>

        <template #default>
          <DocumentRecord />
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