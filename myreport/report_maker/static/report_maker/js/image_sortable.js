(function () {
  function getCsrfToken() {
    // 1) tenta pelo input do template (você já injeta {% csrf_token %})
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input && input.value) return input.value;

    // 2) fallback: cookie (se estiver disponível)
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) return parts.pop().split(";").shift();

    return null;
  }

  function initImageSortable(container) {
    if (typeof Sortable === "undefined") {
      console.error("SortableJS não carregado.");
      return;
    }

    const reorderUrl = container.dataset.reorderUrl;
    if (!reorderUrl) {
      console.error("URL de reorder não definida (data-reorder-url).");
      return;
    }

    new Sortable(container, {
      animation: 150,
      handle: ".js-drag-handle",
      draggable: "[data-image-id]",
      ghostClass: "opacity-50",

      onEnd: async function () {
        const orderedIds = Array.from(container.querySelectorAll("[data-image-id]"))
          .map(el => el.getAttribute("data-image-id"));

        if (!orderedIds.length) return;

        const csrftoken = getCsrfToken();
        if (!csrftoken) {
          console.error("CSRF token não encontrado (cookie e input).");
          return;
        }

        try {
          const resp = await fetch(reorderUrl, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify({ ordered_ids: orderedIds }),
          });

          if (!resp.ok) {
            const txt = await resp.text();
            console.error("Reorder imagens falhou:", resp.status, txt);
          } else {
            // opcional: debug rápido
            // console.log("Reorder imagens OK");
          }
        } catch (err) {
          console.error("Erro de rede ao persistir ordem das imagens:", err);
        }
      },
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('[data-sortable="images"]').forEach(initImageSortable);
  });
})();
