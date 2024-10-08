<script setup lang="ts">
const {
  sortBy
} = storeToRefs(useBcrosDocuments())

const {
  sortSearchTable
} = useDocumentSearch()

const props = defineProps({
  label: {
    type: String,
    require: true,
    default: ''
  }
})

const sortSearchResult = () => {
  if(sortBy.value.column === props.label) {
    sortBy.value.ascending = !sortBy.value.ascending
  } else {
    sortBy.value.column = props.label
    sortBy.value.ascending = true
  }
  sortSearchTable()
}
</script>
<template>
  <UButton 
        class="bg-white text-gray-900 hover:bg-white font-bold"
        :padded="false"
        :label="label"
        @click="sortSearchResult"
  />
</template>