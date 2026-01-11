// (ajustado) - acrescenta deleção de comentários, mantendo seu padrão atual
// :contentReference[oaicite:0]{index=0}

document.addEventListener("DOMContentLoaded", function () {

  /* ==============================
     Validação do formulário de post
     ============================== */
  const form = document.getElementById("post-form");
  const MIN_TEXT_LEN = 10;

  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const titleInput = form.querySelector('[name="title"]');
      const textInput  = form.querySelector('[name="text"]');
      const mediaInput = form.querySelector('[name="media"]');
      const groupInput = form.querySelector('[name="group"]');

      const title = titleInput ? titleInput.value.trim() : "";
      const text  = textInput  ? textInput.value.trim()  : "";
      const media = mediaInput && mediaInput.files ? mediaInput.files.length : 0;

      // validação mínima
      if (!title && !text && !media) {
        alert("Preencha ao menos um dos campos: título, texto ou mídia.");
        return;
      }
      if (text && text.length < MIN_TEXT_LEN) {
        alert(`O texto deve conter ao menos ${MIN_TEXT_LEN} caracteres.`);
        return;
      }

      const errorsBox = document.getElementById("post-form-errors");
      if (errorsBox) errorsBox.innerHTML = "";

      const submitBtn = form.querySelector('button[type="submit"]');
      const cancelBtn = document.getElementById("btnCancelPost");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const resp = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: new FormData(form), // inclui group/title/text/media
        });

        const data = await resp.json().catch(() => ({}));

        if (!resp.ok || !data.success) {
          if (errorsBox) {
            errorsBox.innerHTML =
              data.errors_html ||
              "<div class='alert alert-danger py-2 mb-0'>Erro ao criar postagem.</div>";
          }
          return;
        }

        // insere no topo do feed
        const feed = document.getElementById("posts-feed");
        if (feed && data.html) {
          // remove placeholder "Nenhuma postagem encontrada."
          const placeholder = feed.querySelector(".alert.alert-secondary");
          if (placeholder) placeholder.remove();

          feed.insertAdjacentHTML("afterbegin", data.html);
        }

        // limpa campos
        if (titleInput) titleInput.value = "";
        if (textInput) textInput.value = "";
        if (mediaInput) mediaInput.value = "";
        if (groupInput) groupInput.value = ""; // volta para "Público"

        // fecha o collapse (opcional)
        const collapseEl = document.getElementById("postFormCollapse");
        if (collapseEl && window.bootstrap?.Collapse) {
          bootstrap.Collapse.getOrCreateInstance(collapseEl).hide();
        }

      } catch (err) {
        if (errorsBox) {
          errorsBox.innerHTML =
            "<div class='alert alert-danger py-2 mb-0'>Falha de comunicação.</div>";
        }
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  /* ==============================
     Like via fetch
     ============================== */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".js-like-btn");
    if (!btn) return;

    const url = btn.dataset.likeUrl;
    const icon = btn.querySelector("i");
    const counter = btn.querySelector(".likes-count");

    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(r => r.json())
      .then(data => {
        if (!data.success) return;
        counter.textContent = data.likes_count;
        icon.classList.toggle("bi-heart", !data.liked);
        icon.classList.toggle("bi-heart-fill", data.liked);
        icon.classList.toggle("text-danger", data.liked);
      });
  });

  /* ==============================
     Rating via fetch (dropdown)
     ============================== */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".js-rate-btn");
    if (!btn) return;

    e.preventDefault();

    const url = btn.dataset.rateUrl;
    const value = btn.dataset.value;

    const container = btn.closest(".js-rating-container");
    if (!container) return;

    const mainIcon = container.querySelector(".js-rating-icon");
    const label = container.querySelector(".text-muted"); // "Avaliar" / "Avaliar (x)"

    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      },
      body: `value=${encodeURIComponent(value)}`,
    })
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(data => {
        if (!data.success) return;

        const rated = ("rated" in data) ? !!data.rated : true;
        const currentValue = ("value" in data) ? data.value : value;

        if (mainIcon) {
          mainIcon.classList.toggle("bi-star", !rated);
          mainIcon.classList.toggle("bi-star-fill", rated);
          mainIcon.classList.toggle("text-warning", rated);
        }

        if (label) {
          label.textContent = rated ? `Avaliar (${currentValue})` : "Avaliar";
        }

        // fecha o dropdown após clicar
        const toggle = container.querySelector('[data-bs-toggle="dropdown"]');
        if (toggle && window.bootstrap?.Dropdown) {
          bootstrap.Dropdown.getOrCreateInstance(toggle).hide();
        }
      })
      .catch(err => console.error("Erro ao avaliar:", err));
  });

  /* ==============================
     Comentários: submit via fetch + atualizar lista (mantém só 5 no feed)
     ============================== */
  document.addEventListener("submit", async function (e) {
    const cForm = e.target.closest(".comment-form");
    if (!cForm) return;

    e.preventDefault();

    const postId = cForm.dataset.postId;
    const listEl = document.querySelector(`#commentsList-${postId}`);
    const errorsBox = cForm.querySelector(".comment-errors");

    if (errorsBox) errorsBox.innerHTML = "";

    try {
      const resp = await fetch(cForm.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
        body: new FormData(cForm),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok || !data.success) {
        if (errorsBox) {
          errorsBox.innerHTML =
            data.errors_html ||
            "<div class='alert alert-danger py-2 mb-0'>Erro ao enviar comentário.</div>";
        }
        return;
      }

      if (listEl) {
        // remove placeholder "Nenhum comentário ainda."
        const placeholder = listEl.querySelector("small.text-muted");
        if (placeholder) placeholder.remove();

        // adiciona o novo comentário no topo
        listEl.insertAdjacentHTML("afterbegin", data.html);

        // mantém somente os 5 comentários mais recentes (itens com id="comment-...")
        const items = Array.from(listEl.children).filter(el =>
          el.id && el.id.startsWith("comment-")
        );
        for (let i = 5; i < items.length; i++) items[i].remove();
      }

      // limpa campos
      const ta = cForm.querySelector('textarea[name="text"]');
      if (ta) ta.value = "";

      const file = cForm.querySelector('input[name="image"]');
      if (file) file.value = "";

      const parent = cForm.querySelector('input[name="parent"]');
      if (parent) parent.value = "";

    } catch (err) {
      if (errorsBox) {
        errorsBox.innerHTML =
          "<div class='alert alert-danger py-2 mb-0'>Falha de comunicação.</div>";
      }
    }
  });

  /* ==============================
     Comentários: cancelar (fecha collapse e limpa)
     ============================== */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-cancel-comment");
    if (!btn) return;

    const cForm = btn.closest(".comment-form");
    if (cForm) {
      const errorsBox = cForm.querySelector(".comment-errors");
      if (errorsBox) errorsBox.innerHTML = "";

      const ta = cForm.querySelector('textarea[name="text"]');
      if (ta) ta.value = "";

      const file = cForm.querySelector('input[name="image"]');
      if (file) file.value = "";

      const parent = cForm.querySelector('input[name="parent"]');
      if (parent) parent.value = "";
    }

    const targetSel = btn.dataset.bsTarget;
    if (targetSel && window.bootstrap) {
      const collapseEl = document.querySelector(targetSel);
      if (collapseEl) bootstrap.Collapse.getOrCreateInstance(collapseEl).hide();
    }
  });

  /* ==============================
     Deleção de postagens
     ============================== */
  document.addEventListener("click", async function (e) {
    const btn = e.target.closest(".js-post-delete");
    if (!btn) return;

    const url = btn.dataset.deleteUrl;
    const postId = btn.dataset.postId;

    if (!confirm("Inativar esta postagem?")) return;

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.success) return;

    const card = document.querySelector(`#post-${postId}`);
    if (card) card.remove();
  });



  /* ==============================
     Ocultar postagem (feed do usuário)
     ============================== */
  document.addEventListener("click", async function (e) {
    const btn = e.target.closest(".js-post-hide");
    if (!btn) return;

    const url = btn.dataset.hideUrl;
    const postId = btn.dataset.postId;

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) return;

    // remove visualmente do feed
    const card = document.querySelector(`#post-${postId}`);
    if (card) card.remove();
  });




  /* ==============================
     Deleção de comentários
     ============================== */
  document.addEventListener("click", async function (e) {
    const btn = e.target.closest(".js-comment-delete");
    if (!btn) return;

    const url = btn.dataset.deleteUrl;
    const commentId = btn.dataset.commentId;

    if (!confirm("Inativar este comentário?")) return;

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.success) return;

    const el = document.querySelector(`#comment-${commentId}`);
    if (el) el.remove();
  });

});


function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let c of cookies) {
      c = c.trim();
      if (c.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(c.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}



// static/js/social_net/post_form.js

(function () {
  function initPostMediaPreview() {
    const input = document.querySelector('#post-form input[type="file"][name="media"]');
    if (!input) return;

    const wrapper = document.getElementById('post-media-preview-wrapper');
    const img = document.getElementById('post-media-preview');
    if (!wrapper || !img) return;

    input.addEventListener('change', function () {
      const file = input.files && input.files[0];
      if (!file) {
        img.removeAttribute('src');
        wrapper.classList.add('d-none');
        return;
      }

      // Se não for imagem, só oculta o preview (evita mostrar lixo)
      if (!file.type || !file.type.startsWith('image/')) {
        img.removeAttribute('src');
        wrapper.classList.add('d-none');
        return;
      }

      const url = URL.createObjectURL(file);
      img.src = url;
      wrapper.classList.remove('d-none');

      // libera o blob quando a imagem carregar
      img.onload = function () {
        URL.revokeObjectURL(url);
      };
    });
  }

  document.addEventListener('DOMContentLoaded', initPostMediaPreview);
})();
