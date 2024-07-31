<template>
  <div :data-cy="'document-indexing'" class="grid grid-cols-8 gap-4 mt-12 mb-16">

    <div class="col-span-6">
      <BcrosSection name="documentIndexing">
        <template #header>
          <div class="grid grid-cols-6">
            <div class="col-span-6">
              <h1 class="text-[32px] pb-2">{{ $t('title.documentIndexing') }}</h1>
              <span class="text-gray-700 font-normal text-[16px]">{{ $t('descriptions.documentIndexing') }}</span>
            </div>
          </div>
        </template>

        <template #default>
          <DocumentIndexingForm class="mt-7" />
        </template>
      </BcrosSection>

      <BcrosSection name="documentUpload">
        <template #default>
          <DocumentUpload class="mt-7" />
        </template>
      </BcrosSection>
    </div>

    <div class="col-span-2 pl-6">
      <div class="bg-white h-[200px] bg-white rounded text-center">
        Nav/Actions Placeholder
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>