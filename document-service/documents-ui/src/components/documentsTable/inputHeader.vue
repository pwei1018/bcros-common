<script setup lang="ts">
import { debounce } from 'lodash'
import type { TableColumnIF } from '~/interfaces/table-interfaces'

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
  column: {
    type: Object as PropType<TableColumnIF>,
    default: () => {},
  },
})

const emit = defineEmits(["update:model-value"])
const filterValue = ref('')
const debouncedInput = debounce((newValue) => {
  if(props.modelValue !== newValue.trim()) {
    emit('update:model-value', newValue);
  }
}, 500)

watch(() => props.modelValue, (newValue) => {
  if (filterValue.value !== newValue) {
    filterValue.value = newValue
  }
}, { immediate: true })

watch(filterValue, (newValue) => {
  debouncedInput(newValue)
})
</script>
<template>
  <div>
    <DocumentsTableSortButton :column="column" />
    <UDivider class="my-3 w-full" />
    <div class="h-11">
      <UInput
        v-if="column.key!=='description'"
        v-model="filterValue"
        class="min-w-[190px] w-full px-2 font-light"
        size="md"
        :placeholder="column.label"
        :ui="{
          icon: { trailing: { pointer: '' , wrapper: 'pr-3.5'} },
          size: { md: 'h-[44px]' },
        }"

      >
        <template #trailing>
          <UButton
            v-show="filterValue !== ''"
            color="gray"
            variant="link"
            icon="i-mdi-cancel-circle text-primary"
            :padded="false"
            @click="filterValue = ''"
          />
        </template>
      </UInput>
    </div>
  </div>
</template>
