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
    wrapper = mount(NavFooter, {props: { backBtn: 'Back', nextBtn: 'next', cancelBtn: 'Cancel' }})
  })

  it('renders two buttons: "Save and Record" and "Cancel"', () => {
    // Find the buttons
    const nextButton = wrapper.find('[data-cy="nav-footer-next-btn"]')
    const cancelButton = wrapper.find('[data-cy="nav-footer-cancel-btn"]')
    const backButton = wrapper.find('[data-cy="nav-footer-back-btn"]')

    // Assert both buttons are found
    expect(nextButton.exists()).toBe(true)
    expect(backButton.exists()).toBe(true)
    expect(cancelButton.exists()).toBe(true)
  })

  it('emits "submit" event when "Save and Record" button is clicked', async () => {
    // Find the "Save and Record" button
    const nextButton = wrapper.find('[data-cy="nav-footer-next-btn"]')

    // Trigger click
    await nextButton.trigger('click')

    // Assert that the "submit" event is emitted
    expect(wrapper.emitted('next')).toBeTruthy()
    expect(wrapper.emitted('next').length).toBe(1)
  })

  it('emits "submit" event when "Back" button is clicked', async () => {
    // Find the "Save and Record" button
    const backButton = wrapper.find('[data-cy="nav-footer-back-btn"]')

    // Trigger click
    await backButton.trigger('click')

    // Assert that the "submit" event is emitted
    expect(wrapper.emitted('back')).toBeTruthy()
    expect(wrapper.emitted('back').length).toBe(1)
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
