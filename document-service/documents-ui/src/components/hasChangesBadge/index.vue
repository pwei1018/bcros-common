<script setup lang="ts">
import type { PropType } from 'vue';
import { computed } from 'vue'
import type { BaseDataUnionIF } from '~/interfaces/common-interfaces'
import { deepChangesComparison } from '~/utils/commonUtils'

const props = withDefaults(defineProps<{
  action?: string,
  baseline: PropType<BaseDataUnionIF>
  currentState: PropType<BaseDataUnionIF>,
  isCaseSensitive?: boolean
}>(), {
  action: 'CHANGED',
  baseline: null,
  currentState: null,
  isCaseSensitive: false
})

/**
 * Is true when there is a difference between the baseline and current state
 * By default string comparisons are insensitive unless activated by isCaseSensitive Prop
 **/
const hasChanges = computed(() => {
  return deepChangesComparison(props.baseline, props.currentState, props.isCaseSensitive)
})
</script>
<template>
  <UBadge
    v-if="hasChanges"
    id="updated-badge-component"
    variant="solid"
    color="primary"
    class="px-2 max-h-[18px] mt-1"
  >
    <b class="text-[10px]">{{ action }}</b>
  </UBadge>
</template>