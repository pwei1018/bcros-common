# documents-common

This directory contains common Vue components designed for reuse and extension in multiple Nuxt projects.  
Components here should follow best practices for maintainability and flexibility.

## Usage

1. **Copy or import** components from this directory into your Nuxt project.
2. **Extend or customize** as needed for your specific use case.
3. **Register components** in your Nuxt project for auto-import or manual usage.

## Guidelines

- Components should be self-contained and documented.
- Avoid project-specific logic; keep components generic.
- Use TypeScript for type safety where possible.
- Follow Nuxt and Vue conventions for file structure and naming.

## Using as an External Layer

To use a component:

To use `documents-common` as an external Nuxt layer (such as from a package or another repository):

1\. Install `documents-common` as a dependency \(via npm, Git, or workspace\)\.

```json
// package.json
{
  "dependencies": {
    "documents-common": "^1.0.0"
  }
}
```
To use `documents-common` directly from a Git repository, specify the repo URL in your `package.json` dependencies, then reference it in `nuxt.config.ts`. Here’s how:

**Example: Install from Git and use as a layer**

```json
// package.json
{
  "dependencies": {
    "documents-common": "git+https://github.com/your-org/documents-common.git"
  }
}
```

2\. Reference the package in your `nuxt.config.ts`:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  layers: [
    { src: 'documents-common' } // Uses the installed Git repo as a layer
  ]
})
```

**Explanation:**
- Add the Git repo to your dependencies.
- Nuxt will resolve the layer from `node_modules/documents-common`.
- You can then import components using the Nuxt alias as shown previously.

3\. Import components or composables using the Nuxt alias:

```vue
<script setup lang="ts">
import PlaygroundTest from '#documents-common/components/PlaygroundTest.vue'
</script>

<template>
  <PlaygroundTest />
</template>
```

**Notes:**  
\- Use the package name or alias instead of a relative path.  
\- The `#documents-common` alias is available if the layer is registered correctly.  
\- This approach works for monorepos, npm packages, or Git dependencies.

Add this section after your existing usage and guidelines.

## Contribution

- Add new components in the `components` directory.
- Update this README with usage instructions for new components.
- Ensure compatibility with Nuxt 3 and Vue 3.
