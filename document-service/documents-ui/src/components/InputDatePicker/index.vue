<script setup lang="ts">
import { format } from 'date-fns'
import type { PropType } from 'vue'
import type { DatePickerDate } from 'v-calendar/dist/types/src/use/datePicker'

const emit = defineEmits(['update:modelValue'])

const props = defineProps({
  modelValue: {
    type: [String, Date] as PropType<DatePickerDate>,
    default: null
  }
})

const date = ref(props.modelValue)
watch(date, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>
<template>
  <UPopover :popper="{ placement: 'bottom-start' }">
    <UInput
      class="w-full"
      :placeholder="date ? format(date, 'd MMMM, yyy') : 'Filing Date'"
      type="text"
      icon="i-mdi-calendar"
      :trailing="true"
    />

    <template #panel="{ close }">
      <DatePicker v-model="date" is-required @close="close"/>
    </template>
  </UPopover>
</template>