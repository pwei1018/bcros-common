<script setup lang="ts">
const { initDocumentState, isValidIndexData, saveDocuments } = useDocumentIndexing()
const { validateIndex, isLoading, displayDocumentReview } = storeToRefs(useBcrosDocuments())
onMounted(() => { initDocumentState() })
onUnmounted(() => { initDocumentState() })

</script>
<template>
  <div :data-cy="'document-indexing'" class="grid grid-cols-8 gap-4 mt-12 mb-16">

    <!-- Loading Overlay and Spinner -->
    <template v-if="isLoading">
      <div class="fixed left-0 top-0 h-full w-full z-50 bg-gray-300 opacity-45" />
      <UIcon
        name="i-heroicons-arrow-path"
        class="animate-spin text-[50px] text-blue-500 absolute top-40 left-[50%]"
      />
    </template>

    <!-- Document Review Modal -->
    <DocumentReviewModal />

    <div class="col-span-6">
      <BcrosSection name="documentIndexing">
        <template #header>
          <div class="grid grid-cols-6">
            <div class="col-span-6">
              <h1 class="text-[32px] pb-2" @click="displayDocumentReview = true">{{ $t('title.documentIndexing') }}</h1>
              <span class="text-gray-700 font-normal text-[16px]">{{ $t('descriptions.documentIndexing') }}</span>
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