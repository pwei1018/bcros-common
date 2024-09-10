import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DocumentRecords from '~/pages/DocumentRecords.vue'
import { mockedI18n } from '~~/tests/test-utils/mockedi18n'
import { BcrosSection, DocumentRecord, NavActionsAside } from '#components'

describe('DocumentRecords', () => {
  it('renders the component and displays the correct content', () => {
    const wrapper = mount(DocumentRecords, { global: { plugins: [mockedI18n] } })
    // Verify the main container is rendered
    expect(wrapper.find('[data-cy="document-records"]').exists()).toBe(true)

    // Verify the BcrosSection component is rendered
    const bcrosSection = wrapper.findComponent(BcrosSection)
    expect(bcrosSection.exists()).toBe(true)

    // Verify the DocumentRecord component is rendered
    const documentRecord = wrapper.findComponent(DocumentRecord)
    expect(documentRecord.exists()).toBe(true)

    // Verify the NavActionsAside component is not rendered
    const navActionsAside = wrapper.findComponent(NavActionsAside)
    expect(navActionsAside.exists()).toBe(false)

    wrapper.unmount()
  })

  it('renders the NavActionsAside component when condition is met', async () => {
    const wrapper = mount(DocumentRecords, { global: { plugins: [mockedI18n] } })
    wrapper.vm.showNavActions = true
    await nextTick()

    // Verify the NavActionsAside component is rendered
    const navActionsAside = wrapper.findComponent(NavActionsAside)
    expect(navActionsAside.exists()).toBe(true)

    wrapper.unmount()
  })
})
