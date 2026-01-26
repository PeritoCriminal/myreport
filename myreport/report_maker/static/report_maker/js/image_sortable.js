;(function () {
  function getCsrfToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]')
    if (input && input.value) return input.value

    const value = `; ${document.cookie}`
    const parts = value.split(`; csrftoken=`)
    if (parts.length === 2) return parts.pop().split(';').shift()

    return null
  }

  function initImageSortable(container) {
    if (typeof Sortable === 'undefined') {
      console.error('SortableJS não carregado.')
      return
    }

    const reorderUrl = container.dataset.reorderUrl
    if (!reorderUrl) return

    const items = container.querySelectorAll('.js-image-card')
    if (items.length < 2) return

    // DEBUG rápido (depois pode remover)
    console.log('[images-sortable] init', { items: items.length, reorderUrl })

    Sortable.create(container, {
      animation: 150,
      handle: '.js-img-drag-handle',
      draggable: '.js-image-card',
      ghostClass: 'opacity-50',
      chosenClass: 'opacity-75',
      forceFallback: true, // <- força funcionar mesmo quando HTML5 drag falha

      onEnd: async function () {
        const orderedIds = Array.from(container.querySelectorAll('.js-image-card'))
          .map((el) => el.dataset.imageId)
          .filter(Boolean)

        if (!orderedIds.length) return

        const csrftoken = getCsrfToken()
        if (!csrftoken) return

        const resp = await fetch(reorderUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
          },
          body: JSON.stringify({ ordered_ids: orderedIds }),
        })

        if (!resp.ok) {
          console.error('Reorder imagens falhou:', resp.status, await resp.text())
        }
      },
    })
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-sortable="images"]').forEach(initImageSortable)
  })
})()
