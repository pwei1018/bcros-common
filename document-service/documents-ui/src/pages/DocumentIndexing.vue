<script setup lang="ts">
const { isValidIndexData } = useDocuments()
const { validateIndex } = storeToRefs(useBcrosDocuments())

</script>
<template>
  <div
    class="grid grid-cols-8 gap-4 mt-12 mb-16"
    :data-cy="'document-indexing'"
  >
    <!-- Document Review Modal -->
    <DocumentReviewModal />

    <div class="col-span-6">
      <BcrosSection name="documentIndexing">
        <template #header>
          <div class="grid grid-cols-6">
            <div class="col-span-6">
              <h1 class="text-[32px] pb-2">{{ $t('title.documentIndexing') }}</h1>
              <span class="text-gray-700 font-normal text-base">{{ $t('descriptions.documentIndexing') }}</span>
            </div>
          </div>
        </template>

        <template #default>
          <DocumentIndexingForm
            class="mt-7"
            :class="(validateIndex && !isValidIndexData) ? 'border-error-left' : ''"
            :validate="validateIndex"
          />
        </template>
      </BcrosSection>

      <BcrosSection name="documentUpload">
        <template #default>
          <DocumentUpload
            class="mt-7"
            :validate="validateIndex"
          />
        </template>
      </BcrosSection>
    </div>

    <div class="col-span-2 pl-6"/>
  </div>
</template>