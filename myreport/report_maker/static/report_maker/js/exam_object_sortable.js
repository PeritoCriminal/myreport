;(function () {
  function getCsrfToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]')
    if (input && input.value) return input.value

    const value = `; ${document.cookie}`
    const parts = value.split(`; csrftoken=`)
    if (parts.length === 2) return parts.pop().split(';').shift()

    return null
  }

  function initExamObjectSortable(container) {
    if (typeof Sortable === 'undefined') {
      console.error('SortableJS não carregado.')
      return
    }

    const reorderUrl = container.dataset.reorderUrl
    if (!reorderUrl) return

    const itemsEls = container.querySelectorAll('.list-group-item[data-id]')
    if (itemsEls.length < 2) return

    console.log('[exam-objects-sortable] init', {
      items: itemsEls.length,
      reorderUrl,
      groupKey: container.dataset.groupKey,
    })

    Sortable.create(container, {
      animation: 150,
      handle: '.js-drag-handle',
      draggable: '.list-group-item',
      ghostClass: 'opacity-50',
      chosenClass: 'opacity-75',
      forceFallback: true,

      onEnd: async function () {
        const ids = Array.from(container.querySelectorAll('.list-group-item[data-id]'))
          .map((el) => el.dataset.id)
          .filter(Boolean)

        if (!ids.length) return

        const csrftoken = getCsrfToken()
        if (!csrftoken) return

        // ✅ contrato do backend: {"items":[{"id":...}, ...]}
        const payload = { items: ids.map((id) => ({ id })) }

        const resp = await fetch(reorderUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
          },
          body: JSON.stringify(payload),
        })

        if (!resp.ok) {
          console.error('Reorder objetos falhou:', resp.status, await resp.text())
        } else {
          // opcional: log do retorno
          // console.log(await resp.json())
        }
      },
    })
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.js-exam-objects-list').forEach(initExamObjectSortable)
  })
})()