import { beforeAll, beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { mockedI18n } from '~~/tests/test-utils/mockedi18n'
import { DocumentRecord } from '#components'

const mockDocumentRecord = {
  consumerDocumentId: "0100000056",
  consumerFilename: "Example2.pdf",
  consumerFilingDateTime: "2024-08-23T19:00:00+00:00",
  consumerIdentifier: "NR123",
  createDateTime: "2024-08-13T17:55:41+00:00",
  documentClass: "NR",
  documentServiceId: "DS0000100059",
  documentType: "NR_MISC",
  documentTypeDescription: "Name requests miscellaneous documents",
  consumerFilenames: ["Example1.pdf", "Example2.pdf"],
  documentUrls: ["https://mockurl.com", "https://mockurl.com"],
  accessionNumber: '123456',
  batchId: 'batch-001',
  pageCount: 10,
  scanDateTime: '2024-08-23',
  author: 'Author Name'
}

const mockDocumentRecordList = [
  { name: mockDocumentRecord.consumerFilenames[0] },
  { name: mockDocumentRecord.consumerFilenames[1] }
]

describe('DocumentRecord', () => {
  let wrapper
  beforeAll(() => {
    const { documentRecord, documentList, scanningDetails } = storeToRefs(useBcrosDocuments())
    documentRecord.value = { ...mockDocumentRecord }
    scanningDetails.value = {
      scanDateTime: mockDocumentRecord.scanDateTime,
      accessionNumber: mockDocumentRecord.accessionNumber,
      batchId: mockDocumentRecord.batchId,
      pageCount: mockDocumentRecord.pageCount,
      author: mockDocumentRecord.author
    }
    documentList.value = mockDocumentRecordList
  })
  beforeEach(async () => {
    wrapper = mount(DocumentRecord, { global: { plugins: [mockedI18n] } })
    await nextTick()
  })

  it('displays the document filenames correctly', async () => {
    // Verify the document filenames are rendered correctly
    const fileLinks = wrapper.findAll('.spanLink')
    expect(fileLinks.length).toBe(2)
    expect(fileLinks[0].text()).toBe('Example1.pdf')
    expect(fileLinks[1].text()).toBe('Example2.pdf')
  })

  it('renders the Scanning Information section correctly when data is present', async () => {
    // Verify the scanning information fields are rendered correctly
    expect(wrapper.text()).toContain('123456')
    expect(wrapper.text()).toContain('batch-001')
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('August 23, 2024')
    expect(wrapper.text()).toContain('Author Name')
  })
})
