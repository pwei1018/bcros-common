<script setup lang="ts">
import { documentTypes } from "~/utils/documentTypes"
const entityTypes = ref([])

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
    default: "",
  },
  isFilter: {
    type: Boolean,
    required: false,
    default: false
  }
})
const emit = defineEmits(["update:model-value"])

const documentClass = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:model-value', value)
  }
})

const clearModelValue = (event) => {
  emit('update:model-value', '')
  event.stopPropagation()
}

onMounted(() => {
  // Insert empty options to document types for break lines on entity type.
  let currentRegistry = documentTypes[0].documents[0].productCode
  documentTypes.forEach((docType) => {
    // Insert empty option before new productCode(registry).
    if (
      currentRegistry !== docType.documents[0].productCode &&
      docType.documents[0].productCode !== "nro"
    ) {
      entityTypes.value.push({
        class: "BreakLine",
        description: "",
        disabled: true,
      })
      currentRegistry = docType.documents[0].productCode
    }
    entityTypes.value.push(docType)
  })
})

watch(documentClass, (newValue) => {
  emit("update:model-value", newValue)
})
</script>
<template>
  <USelectMenu
    v-model="documentClass"
    :placeholder="isFilter 
      ? $t('documentSearch.table.headers.entityType')
      : $t('documentIndexing.form.selectMenu.categoryLabel')"
    class="text-gray-700 font-light w-[300px]"
    :options="entityTypes"
    value-attribute="class"
    option-attribute="description"
    :size="isFilter ? 'md' : 'lg'"
    :ui="{
      icon: { trailing: { pointer: '' } },
      size: { md: 'h-[44px]' },
    }"
    :ui-menu="{
      height: 'max-h-65 h-[400px] w-full',
      option: {
        base: 'h-fit',
        padding: 'p-0',
        container: 'w-full h-fit',
      },
    }"
  >
    <template #option="{ option }">
      <UDivider v-if="option.class === 'BreakLine'" />
      <span v-else class="truncate px-3 py-2 h-[44px] flex items-center">{{
        option.description
      }}</span>
    </template>
    <template #trailing>
      <UButton
        v-if="isFilter"
        v-show="modelValue !== ''"
        variant="link"
        icon="i-mdi-cancel-circle text-primary"
        :padded="false"
        @click.stop="clearModelValue"
      />
      <UIcon name="i-mdi-arrow-drop-down" class="w-5 h-5 text-gray-700" />
    </template>
  </USelectMenu>
</template>
