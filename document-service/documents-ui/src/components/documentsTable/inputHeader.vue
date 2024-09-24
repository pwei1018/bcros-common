<script setup lang="ts">
import type { TableColumnIF } from "~/interfaces/table-inferface";



const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  column: {
    type: Object as PropType<TableColumnIF>,
    default: () => {},
  },
});

const emit = defineEmits(["update:model-value"]);

const filerValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:model-value', value)
})

</script>
<template>
  <div>
    <div class="flex align-center px-2">
      {{ column.label }}
      <UTooltip
        v-if="column.tooltipText"
        :popper="{ placement: 'top', arrow: true}"
        :text="column.tooltipText"
      >
        <UIcon
          name="i-mdi-information-outline"
          class="font-bold w-5 h-5 mx-2"
        />
      </UTooltip>
    </div>
    <UDivider class="my-3 w-full" />
    <div class="h-8">
      <UInput
        v-model="filerValue"
        class="w-full px-2 font-light"
        size="md"
        :placeholder="column.label"
        :ui="{ icon: { trailing: { pointer: ''} } }"
      >
        <template #trailing>
          <UButton
            v-show="filerValue !== ''"
            color="gray"
            variant="link"
            icon="i-mdi-cancel-circle text-primary"
            :padded="false"
            @click="filerValue = ''"
          />
        </template>
      </UInput>
    </div>
  </div>
</template>
