/**
 * Returns a debounced version of a function, delaying its execution until after a timeout.
 * 
 * @param func - The function to debounce.
 * @param timeout - The number of milliseconds to delay execution (default is 200).
 * @returns A debounced version of the provided function.
 */
export function debounce(func, timeout = 200) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      func(...args);
    }, timeout);
  };
}