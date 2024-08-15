<script setup lang="ts">
const { resetStore } = useBcrosDocuments()
const { isValidIndexData, saveDocuments } = useDocuments()
const { validateIndex, displayDocumentReview } = storeToRefs(useBcrosDocuments())
// Use onScopeDispose to reset the store when the component is unmounted
onMounted(() => { resetStore() })
// Reset the store when the component is unmounted or scope is disposed
onScopeDispose(() => { resetStore() })

</script>
<template>
  <div :data-cy="'document-indexing'" class="grid grid-cols-8 gap-4 mt-12 mb-16">
    <!-- Document Review Modal -->
    <DocumentReviewModal />

    <div class="col-span-6">
      <BcrosSection name="documentIndexing">
        <template #header>
          <div class="grid grid-cols-6">
            <div class="col-span-6">
              <h1 class="text-[32px] pb-2" @click="displayDocumentReview = true">{{ $t('title.documentIndexing') }}</h1>
              <span class="text-gray-700 font-normal text-base">{{ $t('descriptions.documentIndexing') }}</span>
            </div>
          </div>
        </template>

        <template #default>
          <DocumentIndexingForm
            class="mt-7"
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

    <div class="col-span-2 pl-6">
      <NavActionsAside
        :validation-error="validateIndex && !isValidIndexData"
        @cancel="navigateTo({ name: RouteNameE.DOCUMENT_MANAGEMENT })"
        @submit="saveDocuments"
      />
    </div>
  </div>
</template>