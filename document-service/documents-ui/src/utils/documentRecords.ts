/** The number of documents per page on document records table */
export const pageSize = 100

/**
 * Truncates a string either by the end or the middle based on the presence of `backChars`.
 * If `backChars` is not specified, it truncates the string from the end and adds '...'.
 * If `backChars` is specified, it truncates from the middle, keeping a specified number 
 * of characters from both the front and back, with '...' in the middle.
 *
 * @param {string} str - The original string to be truncated.
 * @param {number} maxLength - The maximum length of the truncated string, including '...'.
 * @param {number} frontChars - The number of characters to keep at the beginning of the string.
 * @param {number} [backChars] - Optional. The number of characters to keep at the end of the string. 
 *                              If not provided, truncates from the end.
 * @returns {string} - The truncated string with either '...' at the end or in the middle.
 */
export function truncate(str: string, maxLength: number, frontChars: number, backChars: number = undefined) {
  if (str.length <= maxLength) return str;

  if (typeof backChars === 'undefined') {
    // End truncation if backChars is not specified
    return str.slice(0, frontChars) + '...';
  }

  // Middle truncation if backChars is specified
  const front = str.slice(0, frontChars);
  const back = str.slice(-backChars);
  return `${front}...${back}`;
}

/**
 * Generates a preview URL for a given file.
 * 
 * This function creates a URL that can be used to preview a file (e.g., an image, video, or document)
 * in the browser. The URL is tied to the file object and is only valid for the current session.
 * 
 * @param {File} file - The file object for which to generate a preview URL. This is typically obtained
 * from an input element of type "file".
 * @returns {string} - A string representing the object URL that can be used to preview the file.
 */
export function documentPreview (file) {
  return URL.createObjectURL(file)
}