import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { DocumentUpload } from '#components'
import { mockedI18n } from '~~/tests/test-utils/mockedi18n'

describe('DocumentUpload Component', () => {
  let wrapper: ReturnType<typeof mount>
  const { documentList } = storeToRefs(useBcrosDocuments())
  const mockFile = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' })
  const invalidFile = new File(['dummy content'], 'test.txt', { type: 'text/plain' })
  const largeFile = new File(['a'.repeat(51 * 1024 * 1024)], 'largeFile.pdf', { type: 'application/pdf' })


  beforeEach(() => {
    wrapper = mount(DocumentUpload, {
      global: {
        plugins: [mockedI18n],
      },
    })
  })

  afterEach(() => {
    documentList.value = []
    wrapper.unmount()
  })

  it('renders correctly', () => {
    expect(wrapper.find('h3').text()).toBe('Upload Documents')
  })

  it('uploads valid files correctly', async () => {
    wrapper.vm.uploadFile([mockFile])
    await nextTick()

    expect(wrapper.vm.fileError).toBeNull()
    expect(wrapper.vm.documentList.length).toBe(1)
    expect(wrapper.vm.documentList[0].name).toBe('test.pdf')
  })

  it('shows error when uploading a file with invalid type', async () => {
    wrapper.vm.uploadFile([invalidFile])
    await nextTick()

    expect(wrapper.vm.fileError).toBe('Documents must be of PDF file type')
    expect(wrapper.vm.documentList.length).toBe(0)
  })

  it('shows error when uploading a file with size greater than 50MB', async () => {
    wrapper.vm.uploadFile([largeFile])
    await nextTick()

    expect(wrapper.vm.fileError).toBe('Documents exceeds maximum 50 MB file size')
    expect(wrapper.vm.documentList.length).toBe(0)
  })

  it('removes a file from the document list when remove button is clicked', async () => {
    wrapper.vm.uploadFile([mockFile])
    await nextTick()

    expect(wrapper.vm.documentList.length).toBe(1)

    const removeButton = wrapper.find('button')
    await removeButton.trigger('click')

    expect(wrapper.vm.documentList.length).toBe(0)
  })
})
