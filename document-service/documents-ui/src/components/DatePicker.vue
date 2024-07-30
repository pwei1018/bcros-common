<script setup lang="ts">
import { DatePicker as VCalendarDatePicker } from 'v-calendar'
import type { DatePickerDate, DatePickerRangeObject } from 'v-calendar/dist/types/src/use/datePicker'
import 'v-calendar/dist/style.css'
import type { PropType } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Date] as PropType<DatePickerDate | DatePickerRangeObject>,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

const date = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:modelValue', value)
    emit('close')
  }
})

const attrs = {
  transparent: false,
  borderless: false,
  color: 'blue',
  'is-dark': { selector: 'html', darkClass: 'dark' },
  'first-day-of-week': 2,
}
</script>

<template>
  <VCalendarDatePicker v-model="date" v-bind="{ ...attrs, ...$attrs }" />
</template>
