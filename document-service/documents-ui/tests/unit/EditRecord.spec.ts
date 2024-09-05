import { describe, it, beforeEach, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { mockedI18n } from '~~/tests/test-utils/mockedi18n'
import { storeToRefs } from 'pinia'
import { useBcrosDocuments } from '~/stores/documents'
import EditRecord from '~/components/documentRecord/EditRecord.vue'
import { FormWrapper, InputDatePicker, UCheckbox, UInput, USelectMenu, UTextarea } from '#components'

describe('DocumentRecordComponent', () => {
  let wrapper

  // Mock the store and set default values
  beforeEach(() => {
    const { documentRecord, noIdCheckbox, noDocIdCheckbox } = storeToRefs(useBcrosDocuments())

    // Mock the document record state
    documentRecord.value = {
      consumerDocumentId: '',
      consumerIdentifier: '',
      documentClass: '',
      documentType: '',
      consumerFilingDateTime: '',
      documentDescription: ''
    }

    noIdCheckbox.value = false
    noDocIdCheckbox.value = false

    wrapper = mount(EditRecord, {
      global: {
        plugins: [mockedI18n]
      }
    })
  })

  it('renders form inputs correctly', () => {
    // Check if the form inputs are rendered
    expect(wrapper.findComponent(FormWrapper).exists()).toBe(true)
    expect(wrapper.findComponent(UInput).exists()).toBe(true)
    expect(wrapper.findComponent(UCheckbox).exists()).toBe(true)
    expect(wrapper.findComponent(USelectMenu).exists()).toBe(true)
    expect(wrapper.findComponent(UTextarea).exists()).toBe(true)
    expect(wrapper.findComponent(InputDatePicker).exists()).toBe(true)
  })

  it('updates noIdCheckbox state when checkbox is clicked', async () => {
    const noIdCheckbox = wrapper.findAllComponents(UCheckbox).at(1)

    expect(noIdCheckbox.props('modelValue')).toBe(false)

    // Click the checkbox
    await noIdCheckbox.setValue(true)
    expect(noIdCheckbox.props('modelValue')).toBe(true)
  })

  it('updates noDocIdCheckbox state when checkbox is clicked', async () => {
    const noDocIdCheckbox = wrapper.findAllComponents(UCheckbox).at(0)

    expect(noDocIdCheckbox.props('modelValue')).toBe(false)

    // Click the checkbox
    await noDocIdCheckbox.setValue(true)
    expect(noDocIdCheckbox.props('modelValue')).toBe(true)
  })
})
