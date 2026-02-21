// report_maker/static/report_maker/js/text_block_ai.js
(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function getCsrfToken() {
    const fromCookie = getCookie("csrftoken");
    if (fromCookie) return fromCookie;

    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : null;
  }

  function getModalParts() {
    const modalEl = document.getElementById("aiTextBlockModal");
    const outputEl = document.getElementById("aiTextBlockModalOutput");
    const errorEl = document.getElementById("aiTextBlockModalError");
    const applyBtn = document.getElementById("aiTextBlockModalApply");
    const canUseBootstrapModal = !!(window.bootstrap && window.bootstrap.Modal);

    const hasModal = !!(modalEl && outputEl && errorEl && applyBtn && canUseBootstrapModal);
    return { hasModal, modalEl, outputEl, errorEl, applyBtn };
  }

  function showModal(modalEl) {
    const instance = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    instance.show();
  }

  function hideModal(modalEl) {
    const instance = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    instance.hide();
  }

  function setModalError(errorEl, msg) {
    errorEl.textContent = msg;
    errorEl.classList.remove("d-none");
  }

  function clearModalError(errorEl) {
    errorEl.textContent = "";
    errorEl.classList.add("d-none");
  }

  let currentTextarea = null;

  async function handle(btn) {
    const reportId = btn.dataset.reportId;
    const url = btn.dataset.aiUrl;
    const kindRaw = btn.dataset.aiKind || "generic";
    const kind = String(kindRaw).trim().toLowerCase() || "generic";
    const target = btn.dataset.aiTarget;

    const textarea = document.getElementById(target) || document.querySelector(`[name="${target}"]`);
    if (!textarea) return;

    // Agora permitimos que 'notes' seja enviado vazio para que o backend devolva orientações
    const notes = (textarea.value || "").trim();
    const csrfToken = getCsrfToken();

    const { hasModal, modalEl, outputEl, errorEl, applyBtn } = getModalParts();

    if (!reportId) {
      console.error("ID do laudo não encontrado (report_id).");
      return;
    }

    if (!csrfToken) {
      if (hasModal) {
        currentTextarea = textarea;
        outputEl.value = "";
        clearModalError(errorEl);
        setModalError(errorEl, "CSRF token não encontrado. Recarregue a página e tente novamente.");
        showModal(modalEl);
      } else {
        alert("CSRF token não encontrado. Recarregue a página e tente novamente.");
      }
      return;
    }

    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Processando..."; // Alterado de "Gerando..." para refletir a análise

    try {
      const resp = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ kind, notes, report_id: reportId }),
      });

      const contentType = resp.headers.get("content-type") || "";
      const raw = await resp.text();

      if (!resp.ok) {
        console.error("IA erro HTTP:", resp.status, raw);
        const msg = `Falha ao processar (HTTP ${resp.status}).`;

        if (hasModal) {
          currentTextarea = textarea;
          outputEl.value = "";
          clearModalError(errorEl);
          setModalError(errorEl, msg);
          showModal(modalEl);
        } else {
          alert(msg);
        }
        return;
      }

      if (!contentType.includes("application/json")) {
        console.error("IA resposta não-JSON:", raw);
        const msg = "Falha ao processar resposta da IA.";

        if (hasModal) {
          currentTextarea = textarea;
          outputEl.value = "";
          clearModalError(errorEl);
          setModalError(errorEl, msg);
          showModal(modalEl);
        } else {
          alert(msg);
        }
        return;
      }

      const data = JSON.parse(raw);
      const generated = (data.text || "").trim();

      if (!hasModal) {
        textarea.value = generated;
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
        textarea.dispatchEvent(new Event("change", { bubbles: true }));
        return;
      }

      currentTextarea = textarea;
      outputEl.value = generated;
      clearModalError(errorEl);
      showModal(modalEl);

      // Garantir handler do Apply (idempotente)
      if (!applyBtn.dataset.bound) {
        applyBtn.dataset.bound = "1";
        applyBtn.addEventListener("click", () => {
          if (!currentTextarea) return;
          const { hasModal: hm, modalEl: me, outputEl: oe } = getModalParts();
          currentTextarea.value = oe.value;
          currentTextarea.dispatchEvent(new Event("input", { bubbles: true }));
          currentTextarea.dispatchEvent(new Event("change", { bubbles: true }));
          if (hm) hideModal(me);
        });
      }

      // Limpar estado ao fechar (idempotente)
      if (!modalEl.dataset.bound) {
        modalEl.dataset.bound = "1";
        modalEl.addEventListener("hidden.bs.modal", () => {
          currentTextarea = null;
          const parts = getModalParts();
          if (parts.hasModal) clearModalError(parts.errorEl);
        });
      }
    } catch (e) {
      console.error("IA exceção JS:", e);
      const msg = "Falha ao processar requisição.";

      if (hasModal) {
        currentTextarea = textarea;
        outputEl.value = "";
        clearModalError(errorEl);
        setModalError(errorEl, msg);
        showModal(modalEl);
      } else {
        alert(msg);
      }
    } finally {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }

  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-ai-generate]");
    if (!btn) return;
    handle(btn);
  });
})();