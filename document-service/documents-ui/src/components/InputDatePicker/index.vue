<script setup lang="ts">
import { format } from 'date-fns'
import type { PropType } from 'vue'
import type { DatePickerDate } from 'v-calendar/dist/types/src/use/datePicker'

const emit = defineEmits(['update:modelValue'])

const props = defineProps({
  modelValue: {
    type: [String, Date] as PropType<DatePickerDate>,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  },
  isRangedPicker: {
    type: Boolean,
    default: false
  }
})

const date = ref(props.modelValue)

const datePlaceholder = computed(() => {
  return props.isRangedPicker
    ? date.value?.end
      ? `${format(date.value?.start, 'd MMMM, yyy')} - ${format(date.value?.end, 'd MMMM, yyy')}`
      : 'Date Range'
    : format(date.value, 'd MMMM, yyy')
})

watch(date, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>
<template>
  <UPopover :popper="{ placement: 'bottom-start' }">
    <UInput
      class="w-full"
      :placeholder="date ? datePlaceholder : 'Filing Date'"
      type="text"
      icon="i-mdi-calendar"
      :disabled="disabled"
      :trailing="true"
    />

    <template #panel="{ close }">
      <DatePicker
        v-model="date"
        :is-ranged-picker="isRangedPicker"
        is-required @close="close"
      />
    </template>
  </UPopover>
</template>