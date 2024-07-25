<template>
  <div class="app-container" data-cy="default-layout">
    <bcros-header />
    <bcros-breadcrumb v-if="crumbConstructors.length" :crumb-constructors="crumbConstructors" />
    <div class="app-inner-container app-body">
      <slot />
    </div>
    <bcros-footer />
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const crumbConstructors = computed(() => (route?.meta?.breadcrumbs || []) as (() => BreadcrumbI)[])
</script>