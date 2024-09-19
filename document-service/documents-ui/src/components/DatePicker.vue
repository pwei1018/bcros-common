<script setup lang="ts">
import { DatePicker as VCalendarDatePicker } from 'v-calendar'
import type { DatePickerDate, DatePickerRangeObject } from 'v-calendar/dist/types/src/use/datePicker'
import { calculatePreviousDate } from '~/utils/dateHelper'
import 'v-calendar/dist/style.css'
import type { PropType } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Date, Object] as PropType<DatePickerDate | DatePickerRangeObject>,
    default: null
  },
  isRangedPicker: {
    type: Boolean,
    default: false
  },
  isLeftBar: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:model-value', 'close'])

const date = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:model-value', value)
    emit('close')
  }
})

const handleSideBar = (option) => {
  emit('update:model-value', {
    start: calculatePreviousDate(option),
    end: new Date()
  })
  emit('close')
}

const attrs = {
  transparent: false,
  borderless: false,
  color: 'blue',
  'is-dark': { selector: 'html', darkClass: 'dark' },
  'first-day-of-week': 2,
}
</script>

<template>
  <div class="flex">
  <div 
    v-if="isLeftBar"
    class="flex gap-y-3 flex-col px-5 items-start justify-center font-light"
  >
    <ULink
      v-for="(option, i) in datePickerOptions"
      :key="i"
      class="block"
      @click="handleSideBar(option.value)"
    >
      {{ option.label }}
    </ULink>

  </div>
  <VCalendarDatePicker
    v-if="date && isRangedPicker && (typeof date === 'object')"
    v-model.range="date"
    :columns="2"
    v-bind="{ ...attrs, ...$attrs }"
    size="md"
  />
  <VCalendarDatePicker
    v-else
    v-model="date"
    v-bind="{ ...attrs, ...$attrs }"
  />
</div>
</template>
