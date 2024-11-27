/**
 * Copies the provided text to the clipboard.
 *
 * @param {string} text - The text to be copied.
 */
export function copyToClipboard(text: string): void {
    if (!navigator.clipboard) {
      console.error('Clipboard API not supported');
      return;
    }
  
    navigator.clipboard.writeText(text)
}