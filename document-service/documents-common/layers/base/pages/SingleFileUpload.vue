<template>
  <FileUpload
    class="mt-10"
    :upload-label="'Singe File Upload'"
    :multiple-files="false"
    :max-file-size="5 * 1024 * 1024"
    :min-dimensions="{ width: 500, height: 500 }"
    :max-dimensions="{ width: 4096, height: 4096 }"
    :accepted-file-types="['image/jpeg', 'image/png', 'application/pdf']"
    @converted-files="console.log('Converted files Emit Event:', $event)"
  />
</template>
