// Drag-to-scroll somente para mouse (PC) em prateleiras horizontais
;(function () {
  const shelves = document.querySelectorAll('[data-shelf]')
  if (!shelves.length) return

  // Em touch/mobile, use scroll nativo (não aplica drag JS)
  const isFinePointer = window.matchMedia('(pointer: fine)').matches
  if (!isFinePointer) return

  shelves.forEach((shelf) => {
    let isDown = false
    let startX = 0
    let scrollLeft = 0

    const onDown = (e) => {
      // evita iniciar arrasto ao clicar em links/botões
      if (e.target.closest('a, button')) return

      isDown = true
      shelf.classList.add('is-dragging')

      // evita seleção/drag de imagem/texto
      e.preventDefault()

      startX = e.pageX - shelf.getBoundingClientRect().left
      scrollLeft = shelf.scrollLeft
    }

    const onMove = (e) => {
      if (!isDown) return
      e.preventDefault()

      const x = e.pageX - shelf.getBoundingClientRect().left
      const walk = (x - startX) * 1.5
      shelf.scrollLeft = scrollLeft - walk
    }

    const stop = () => {
      isDown = false
      shelf.classList.remove('is-dragging')
    }

    shelf.addEventListener('mousedown', onDown, { passive: false })
    shelf.addEventListener('mousemove', onMove, { passive: false })
    shelf.addEventListener('mouseup', stop)
    shelf.addEventListener('mouseleave', stop)

    // impede o browser de “arrastar a imagem” dentro do card
    shelf.addEventListener('dragstart', (e) => e.preventDefault())
  })
})()
