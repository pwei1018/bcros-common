<template>
  <FileUpload
    :upload-label="'Multiple File Upload'"
    @converted-files="console.log('Converted files Emit Event:', $event)"
  />
</template>
