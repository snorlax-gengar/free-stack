import { act } from 'react'
import { vi } from 'vitest'

export function installDialogStub() {
  const originalShowModal = HTMLDialogElement.prototype.showModal
  const originalClose = HTMLDialogElement.prototype.close
  const showModal = vi.fn(function showModal(this: HTMLDialogElement) {
    this.setAttribute('open', '')
  })

  HTMLDialogElement.prototype.showModal = showModal
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    if (!this.open) {
      return
    }
    this.removeAttribute('open')
    const dialog = this
    queueMicrotask(() => {
      dialog.dispatchEvent(new Event('close'))
    })
  }

  return {
    showModal,
    restore() {
      HTMLDialogElement.prototype.showModal = originalShowModal
      HTMLDialogElement.prototype.close = originalClose
    },
  }
}

export async function flushDialogClose(): Promise<void> {
  await act(async () => {
    await Promise.resolve()
  })
}
