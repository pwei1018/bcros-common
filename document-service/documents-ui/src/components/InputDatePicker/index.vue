<script setup lang="ts">
import { format } from "date-fns"
import type { PropType } from "vue"
import type {
  DatePickerDate,
  DatePickerRangeObject,
} from "v-calendar/dist/types/src/use/datePicker"

const emit = defineEmits(["update:modelValue"])

const props = defineProps({
  modelValue: {
    type: [String, Date, Object] as PropType<
      DatePickerDate | DatePickerRangeObject
    >,
    default: null,
  },
  datePlaceholder: {
    type: String,
    default: 'Filing Date',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  isRangedPicker: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: null,
  },
  isFilter: {
    type: Boolean,
    default: false,
  },
  isTrailing: {
    type: Boolean,
    default: false,
  }
})

const date: DatePickerRangeObject | DatePickerDate = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
})

const isDateClearable = computed(() => {
  return props.isRangedPicker
    ? (!!props.modelValue.start || !!props.modelValue.end)
    : !!props.modelValue
})

const datePlaceholder = computed(() => {
  return props.isRangedPicker
    ? date.value?.end
      ? `${format(date.value?.start, "d MMMM, yyy")} - ${format(
          date.value?.end,
          "d MMMM, yyy"
        )}`
      : "Date Range"
    : format(date.value, "d MMMM, yyy")
})

const clearModelValue = (event) => {
  emit('update:modelValue', props.isRangedPicker
    ? { start: null, end: null }
    : "")
  event.stopPropagation()
}
</script>
<template>
  <UPopover :popper="{ placement: 'bottom-start' }">
    <UInput
      class="w-full"
      :placeholder="date ? datePlaceholder : props.datePlaceholder"
      type="text"
      icon="i-mdi-calendar"
      :disabled="disabled"
      :trailing="true"
      :size="size"
      :ui="{
        icon: { trailing: { pointer: '' } },
        size: { md: 'h-[44px]' },
      }"
    >
      <template #trailing>
        <UButton
          v-if="isTrailing || isFilter"
          v-show="isDateClearable"
          color="gray"
          variant="link"
          icon="i-mdi-cancel-circle text-primary"
          :padded="false"
          @click.stop="clearModelValue"
        />
        <UIcon name="i-mdi-calendar" :class="['w-5 h-5', isFilter ? '' : 'text-primary']" />
      </template>
    </UInput>

    <template #panel="{ close }">
      <DatePicker
        v-model="date"
        :is-ranged-picker="isRangedPicker"
        is-required
        :is-filter="isFilter"
        @close="close"
      />
    </template>
  </UPopover>
</template>
