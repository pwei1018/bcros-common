<script setup lang="ts">
const { scanningDetails, scanningDetailsSnapshot } = storeToRefs(useBcrosDocuments())
defineProps({
  validate: {
    type: Boolean,
    default: false
  }
})
</script>
<template>
  <FormWrapper
    name="document-scanning-form"
    class="pl-7"
  >
    <template #label>
      <h3>{{ $t('scanningDetails.title') }}</h3>
      <HasChangesBadge
        :baseline="scanningDetailsSnapshot"
        :current-state="scanningDetails"
      />
    </template>

    <template #form>
      <div class="grid grid-flow-row auto-rows-max">
        <UInput
          v-model="scanningDetails.accessionNumber"
          type="text"
          required
          :placeholder="$t('scanningDetails.accessionNumber')"
        />

        <div class="grid grid-cols-4 gap-5 mt-3">
          <div class="col-span-2">
            <UInput
              v-model="scanningDetails.batchId"
              class="mt-3"
              type="text"
              required
              :placeholder="$t('scanningDetails.batchId')"
            />
          </div>

          <div class="col-span-2">
            <UInput
              v-model="scanningDetails.pageCount"
              class="mt-3"
              type="text"
              required
              :placeholder="$t('scanningDetails.pagesToScan')"
            />
          </div>
        </div>

        <InputDatePicker
          v-model="scanningDetails.scanDateTime"
          :date-placeholder="$t('scanningDetails.scannedDate')"
          class="mt-3"
        />
      </div>
    </template>
  </FormWrapper>
</template>