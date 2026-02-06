// report_maker/static/report_maker/js/text_block_ai.js
(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function getCsrfToken() {
    // 1) cookie (padrão Django)
    const fromCookie = getCookie("csrftoken");
    if (fromCookie) return fromCookie;

    // 2) fallback: input hidden do form (funciona mesmo com CSRF_COOKIE_HTTPONLY=True)
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : null;
  }

  async function handle(btn) {
    const url = btn.dataset.aiUrl;
    const kind = btn.dataset.aiKind || "generic";
    const target = btn.dataset.aiTarget;

    const textarea = document.getElementById(target) || document.querySelector(`[name="${target}"]`);
    if (!textarea) return;

    const notes = (textarea.value || "").trim();
    if (!notes) {
      alert("Digite algumas informações no campo antes de gerar.");
      return;
    }

    const csrfToken = getCsrfToken();
    if (!csrfToken) {
      alert("CSRF token não encontrado. Recarregue a página e tente novamente.");
      return;
    }

    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Gerando...";

    try {
      const resp = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ kind, notes }),
      });

      const contentType = resp.headers.get("content-type") || "";
      const raw = await resp.text();

      if (!resp.ok) {
        console.error("IA erro HTTP:", resp.status, raw);
        alert(`Falha ao gerar texto com IA (HTTP ${resp.status}). Veja o console (F12).`);
        return;
      }

      if (!contentType.includes("application/json")) {
        // geralmente acontece quando veio HTML (ex: redirect/login) ou erro
        console.error("IA resposta não-JSON:", raw);
        alert("Falha ao gerar texto com IA (resposta inesperada). Veja o console (F12).");
        return;
      }

      const data = JSON.parse(raw);
      textarea.value = data.text || "";
      textarea.dispatchEvent(new Event("input", { bubbles: true }));
      textarea.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (e) {
      console.error("IA exceção JS:", e);
      alert("Falha ao gerar texto com IA. Veja o console (F12).");
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
