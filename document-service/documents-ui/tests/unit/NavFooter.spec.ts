import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { NavFooter } from '#components'
import { storeToRefs } from 'pinia'
import { useBcrosDocuments } from '~/stores/documents'

describe('FooterNav.vue', () => {
  let wrapper

  beforeEach(() => {
    const { isEditing } = storeToRefs(useBcrosDocuments())
    isEditing.value = true
    wrapper = mount(NavFooter)
  })

  it('renders two buttons: "Save and Record" and "Cancel"', () => {
    // Find the buttons
    const submitButton = wrapper.find('[data-cy="nav-footer-save-btn"]')
    const cancelButton = wrapper.find('[data-cy="nav-footer-cancel-btn"]')

    // Assert both buttons are found
    expect(submitButton.exists()).toBe(true)
    expect(cancelButton.exists()).toBe(true)
  })

  it('emits "submit" event when "Save and Record" button is clicked', async () => {
    // Find the "Save and Record" button
    const submitButton = wrapper.find('[data-cy="nav-footer-save-btn"]')

    // Trigger click
    await submitButton.trigger('click')

    // Assert that the "submit" event is emitted
    expect(wrapper.emitted('submit')).toBeTruthy()
    expect(wrapper.emitted('submit').length).toBe(1)
  })

  it('emits "cancel" event when "Cancel" button is clicked', async () => {
    // Find the "Cancel" button
    const cancelButton = wrapper.find('[data-cy="nav-footer-cancel-btn"]')

    // Trigger click
    await cancelButton.trigger('click')

    // Assert that the "cancel" event is emitted
    expect(wrapper.emitted('cancel')).toBeTruthy()
    expect(wrapper.emitted('cancel').length).toBe(1)
  })
})
