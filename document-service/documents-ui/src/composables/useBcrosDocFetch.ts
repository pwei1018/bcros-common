import { useBcrosDocuments } from '~/stores/documents'

/**
 * Custom hook utilizes `useFetch` with customized options and a shared Nuxt app fetch instance.
 *
 * @param {string} url - The endpoint URL for the request.
 * @param {any} options - Configuration options for the request.
 * @param {string | undefined} consumerIdentifier - Optional parameter for error reporting.
 * @returns {Promise<T>} - The response, typed as `T`.
 */

export function useBcrosDocFetch<T>(url: string, options: any, consumerIdentifier?: string | undefined) {
    const { isError, errorMsg } = storeToRefs(useBcrosDocuments())
    return useFetch<T>(url, {
      ...options,
      watch: false,
      $fetch: useNuxtApp().$bcrosFetch,
      onResponseError(response) {
        const requestMethod = response.options.method
        if(["POST", "PUT"].includes(requestMethod) && !isError.value){
            const accountId = response.options.headers["Account-Id"]
            // Extract only the base URL, excluding query parameters.
            const url = response.request.toString().split('?')[0]
            const message = JSON.stringify(response.response._data)
            const timeStamp = new Date().toISOString()
            isError.value = true
            errorMsg.value.push(`${accountId}, ${timeStamp} ${consumerIdentifier ? ', ' + consumerIdentifier : ''}`)
            errorMsg.value.push(url)
            errorMsg.value.push(message)
        }
      }
    })
  }
  