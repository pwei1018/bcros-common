<script setup lang="ts">

const props = defineProps({
  isHelpContentOpen: {
    type: Boolean,
    default: false
  },
  hasBottomHideToggle: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggleHelpContent'])
</script>

<template>
  <div class="my-2">
    <ULink
      class="flex items-center text-primary font-bold"
      @click="emit('toggleHelpContent')"
    >
    <UIcon
      name="i-mdi-help-circle-outline"
      class="font-bold w-5 h-5 mx-2"
    />
      <p>{{ $t('documentSearch.helpTitle.inactive') }}</p>
    </ULink>
    <div>
      <div v-show="props.isHelpContentOpen">
        <slot
          name="content"
          class="text-light"
        />
        <div
          v-if="props.hasBottomHideToggle"
          class="float-right"
        >
          <ULink
            class="text-primary text-light underline"
            @click="emit"
          >
          {{ $t('documentSearch.helpTitle.active') }}
          </ULink>
        </div>
      </div>
    </div>
  </div>
</template>
