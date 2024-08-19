/**
 * Converts a date string into an ISO 8601 formatted string with the local timezone offset.
 *
 * @param dateString - The date string to be formatted.
 * @returns The ISO 8601 formatted date string with the correct timezone offset.
 */
export const formatDateToISO = (dateString: string) => {
  const date = new Date(dateString)

  // Format the date to ISO 8601 with timezone offset
  const isoString = date.toISOString()

  // Convert the UTC time to the local time with timezone offset
  const offsetMinutes = date.getTimezoneOffset()
  const offsetHours = Math.floor(Math.abs(offsetMinutes) / 60)
  const minutes = Math.abs(offsetMinutes) % 60
  const sign = offsetMinutes > 0 ? '-' : '+'

  // Create the formatted timezone offset string
  const timezoneOffset = `${sign}${String(offsetHours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`

  // Replace the 'Z' with the correct timezone offset
  return isoString.replace('Z', timezoneOffset)
}

/**
 * Converts an ISO 8601 date string to a human-readable date format.
 *
 * This function formats the given ISO date string into a readable format,
 * such as "August 13, 2024 at 10:21:29 AM Pacific time". The formatting
 * includes the full date, time, and the Pacific time zone.
 *
 * @param isoDate - The ISO 8601 date string to be formatted (e.g., "2024-08-13T17:21:29+00:00").
 * @param omitTime - A flag to determine if the date should be formatted without time.
 * @returns A string representing the formatted date in a readable format with or without time.
 */
export function formatToReadableDate(isoDate: string, omitTime: boolean = false): string {
  const date = new Date(isoDate)

  // Options for formatting the date
  const dateOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }

  // Options for formatting the time
  const timeOptions: Intl.DateTimeFormatOptions = {
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric',
    hour12: true,
    timeZoneName: 'short',
    timeZone: 'America/Los_Angeles', // Pacific Time Zone
  }

  // Format the date
  const formattedDate = new Intl.DateTimeFormat('en-US', dateOptions).format(date)

  // If omitTime is true, return only the date
  if (omitTime) {
    return formattedDate
  }

  // Otherwise, format the date with time
  const formattedTime = new Intl.DateTimeFormat('en-US', timeOptions).format(date)

  // Return the date and time, replacing PDT/PST with 'Pacific time'
  return `${formattedDate} at ${formattedTime.replace(/PDT|PST/, 'Pacific time')}`
}

/**
 * Converts an ISO 8601 date string to YYYY-MM-DD format.
 *
 * @param {string} isoString - The ISO 8601 date string (e.g., '2024-08-01T07:00:00.000Z').
 * @returns {string} - The formatted date in YYYY-MM-DD format.
 */
export function formatIsoToYYYYMMDD(isoString) {
  const date = new Date(isoString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}