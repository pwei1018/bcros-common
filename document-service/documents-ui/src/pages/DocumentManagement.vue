<script setup lang="ts">
import { documentRecordHelpContent } from '~/utils/documentTypes';
const { resetStore } = useBcrosDocuments()
const { documentSearchResults } = storeToRefs(useBcrosDocuments())

const isHelpContentOpen = ref(false)
const hasBottomHideToggle = ref(true)

const toggleHelpContent = () => {
  isHelpContentOpen.value = !isHelpContentOpen.value
}
const launchCreateRecord = () => {
  resetStore()
  navigateTo({ name: RouteNameE.DOCUMENT_INDEXING })
}

</script>
<template>
  <div data-cy="document-management">
    <BcrosSection
      name="documentManagement"
      class="mt-12"
    >
      <template #header>
        <div class="items-center">

          <div>
            <h1 class="text-[32px] pb-2">{{ $t('title.documentManagement') }}</h1>
            <span class="text-gray-700 font-normal text-base">{{ $t('descriptions.documentManagement') }}</span>
          </div>
          <!-- Hiding help button until we get the content -->
          <!-- Help content -->
          <HelpToggleContainer
            :is-help-content-open="isHelpContentOpen"
            :has-bottom-hide-toggle="hasBottomHideToggle"
            @toggle-help-content="toggleHelpContent"
          >
            <template #content>
              <p>
                {{ documentRecordHelpContent }}
              </p>
            </template>
          </HelpToggleContainer>
          <div>
            <UButton
              class="mt-5 py-2 px-6 text-base font-bold"
              outlined
              color="primary"
              @click="launchCreateRecord()"
            >
              <UIcon
                name="i-mdi-plus"
                class="bg-white text-xl"
              />
              {{ $t('button.documentIndexing') }}
            </UButton>
          </div>
        </div>
      </template>
    </BcrosSection>
  
    <!-- Document Search Results -->
    <UDivider v-if="documentSearchResults.length" class="pt-[60px] pb-4" />
    <DocumentsTable />
  </div>
</template>