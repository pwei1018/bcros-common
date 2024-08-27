import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { DocumentsTable } from '#components'
import { mockedI18n } from '~~/tests/test-utils/mockedi18n'
import { formatToReadableDate } from '~/utils/dateHelper'
const { getDocumentDescription } = useDocuments()
const mockDocumentResults = [
  {
    "consumerDocumentId": "0100000056",
    "consumerFilename": "Example2.pdf",
    "consumerFilingDateTime": "2024-08-23T19:00:00+00:00",
    "consumerIdentifier": "NR123",
    "createDateTime": "2024-08-13T17:55:41+00:00",
    "documentClass": "NR",
    "documentServiceId": "DS0000100059",
    "documentType": "NR_MISC",
    "documentTypeDescription": "Name requests miscellaneous documents",
    "consumerFileNames": ["Example1.pdf", "Example2.pdf"],
    "documentUrls": ["https://mockurl.com", "https://mockurl.com"]
  },
  {
    "consumerDocumentId": "0100000056",
    "consumerFilename": "Example2.pdf",
    "consumerFilingDateTime": "2024-08-23T19:00:00+00:00",
    "consumerIdentifier": "NR123",
    "createDateTime": "2024-08-13T17:55:41+00:00",
    "documentClass": "NR",
    "documentServiceId": "DS0000100059",
    "documentType": "NR_MISC",
    "documentTypeDescription": "Name requests miscellaneous documents",
    "consumerFileNames": ["Example1.pdf", "Example2.pdf"],
    "documentUrls": ["https://mockurl.com", "https://mockurl.com"]
  },
  {
    "consumerDocumentId": "0100000056",
    "consumerFilename": "Example2.pdf",
    "consumerFilingDateTime": "2024-08-23T19:00:00+00:00",
    "consumerIdentifier": "NR123",
    "createDateTime": "2024-08-13T17:55:41+00:00",
    "documentClass": "NR",
    "documentServiceId": "DS0000100059",
    "documentType": "NR_MISC",
    "documentTypeDescription": "Name requests miscellaneous documents",
    "consumerFileNames": ["Example1.pdf", "Example2.pdf"],
    "documentUrls": ["https://mockurl.com", "https://mockurl.com"]
  }
]


describe('DocumentsTable', () => {
  it('Displays expected content', () => {
    const { documentSearchResults } = storeToRefs(useBcrosDocuments())
    documentSearchResults.value = mockDocumentResults

    const wrapper = mount(DocumentsTable, { global: { plugins: [mockedI18n] } })

    // Verify the table is rendered
    expect(wrapper.find('[data-cy="document-search-results"]').exists()).toBe(true)

    // Verify the correct number of rows
    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBe(mockDocumentResults.length)

    // Verify the first row's content
    const firstRowCells = rows[0].findAll('td')
    expect(firstRowCells[0].text()).toBe(mockDocumentResults[0].consumerIdentifier)
    expect(firstRowCells[1].text()).toBe(mockDocumentResults[0].consumerDocumentId)
    expect(firstRowCells[2].text()).toBe(getDocumentDescription('NR'))
    expect(firstRowCells[3].text()).toBe(mockDocumentResults[0].documentTypeDescription)
    expect(firstRowCells[4].text()).toContain(formatToReadableDate('2024-08-23T19:00:00+00:00', true))

    wrapper.unmount()
  })
})