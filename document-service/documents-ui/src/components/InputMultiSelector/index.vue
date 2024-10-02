<script setup lang="ts">
const props = defineProps({
  options: {
    type: Array as PropType<any>,
    required: true,
  },
  valueAttribute: {
    type: String,
    required: true,
  },
  optionAttribute: {
    type: String,
    required: true,
  },
  label: {
    type: String,
    required: false,
    default: "",
  },
})
const emit = defineEmits(["changeColumns"])

const selected = ref([])

onMounted(() => {
  try {
    selected.value = props.options.map((option) => option[props.valueAttribute])
  } catch (error) {
    console.error(error)
  }
})
</script>
<template>
  <USelectMenu
    v-model="selected"
    class="text-gray-700 text-light"
    :placeholder="label"
    :options="options"
    :value-attribute="valueAttribute"
    :option-attribute="optionAttribute"
    size="md"
    multiple
    :ui="{
      icon: { trailing: { pointer: '' } },
      size: { md: 'h-[44px]' },
    }"
    trailing-icon="i-mdi-arrow-drop-down"
    @change="emit('changeColumns', selected)"
  >
    <template v-if="label" #label>
      <span>{{ $t("documentSearch.table.headers.columnsToShow") }}</span>
    </template>
    <template #option="optionProps">
      <UCheckbox
        v-model="optionProps.selected"
        :name="optionProps.option[valueAttribute]"
        :label="optionProps.option[optionAttribute]"
      />
    </template>
  </USelectMenu>
</template>
