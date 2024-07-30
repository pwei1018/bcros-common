<template>
  <BcrosSection name="documentManagement" class="mt-12 mb-16" data-cy="document-management">
    <template #header>
      <div class="grid grid-cols-6 gap-4 items-center">

        <div class="col-start-1 col-end-5">
          <h1 class="text-[32px] pb-2">{{ $t('title.documentManagement') }}</h1>
          <span class="text-gray-700 font-normal text-[16px]">{{ $t('descriptions.documentManagement') }}</span>
        </div>

        <div class="col-end-7 col-span-1">
          <UButton
            class="py-2 px-4 text-[14px] font-bold"
            outlined
            color="primary"
            @click="navigateTo({ name: RouteNameE.DOCUMENT_INDEXING })"
          >
            {{ $t('button.documentIndexing') }}
            <UIcon
              name="i-mdi-chevron-right"
              class="bg-white text-xl"
            />
          </UButton>
        </div>
      </div>
    </template>
    <template #default>
      <div class="h-[550px] p-8 mt-7">
        <!--- Document Management Content -->
        <!--- Will include Search and Results Components -->
        Document Search and Results Placeholder
      </div>
    </template>
  </BcrosSection>
</template>

<script setup lang="ts">
</script>
