<script setup lang="ts">
const { sortBy } = storeToRefs(useBcrosDocuments())

const { sortSearchTable } = useDocumentSearch()

const props = defineProps({
  column: {
    type: Object as PropType<TableColumnIF>,
    require: true,
    default: () => {},
  },
})

const sortSearchResult = () => {
  if (sortBy.value.column === props.column.key) {
    sortBy.value.ascending = !sortBy.value.ascending
  } else {
    sortBy.value.column = props.column.key
    sortBy.value.ascending = true
  }
  sortSearchTable()
}
</script>
<template>
  <div class="flex align-center px-2">
    <UButton
      class="bg-white text-gray-900 hover:bg-white gap-x-2.5"
      :padded="false"
      @click="sortSearchResult"
    >
      <p class="font-bold">
        {{ column.label }}
      </p>
      <UTooltip
        v-if="column.tooltipText"
        :popper="{ placement: 'top', arrow: true }"
        :text="column.tooltipText"
        :ui="{ base: 'w-[265px]' }"
      >
        <UIcon
          name="i-mdi-information-outline"
          class="w-5 h-5 mr-1 text-primary"
        />
      </UTooltip>
      <UIcon
        v-if="sortBy.column === props.column.key"
        :name="sortBy.ascending ? 'i-mdi-arrow-up' : 'i-mdi-arrow-down'"
        class="w-5 h-5 text-primary"
      />
    </UButton>
  </div>
</template>
