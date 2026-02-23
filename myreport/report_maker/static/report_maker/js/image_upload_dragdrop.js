(function () {
    "use strict";

    // Reutiliza a lógica de CSRF robusta presente nos seus outros scripts
    function getCsrfToken() {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input && input.value) return input.value;

        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const zones = document.querySelectorAll(".js-drag-drop-zone");

    zones.forEach((zone) => {
        // 1. Previne comportamentos padrão do browser
        ["dragenter", "dragover", "dragleave", "drop"].forEach((name) => {
            zone.addEventListener(name, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // 2. Feedback Visual: Drag Over
        zone.addEventListener("dragover", () => {
            zone.classList.add("border-primary", "bg-light");
            zone.style.borderStyle = "dashed";
        });

        zone.addEventListener("dragleave", () => {
            zone.classList.remove("border-primary", "bg-light");
            zone.style.borderStyle = "transparent";
        });

        // 3. Evento de Soltar (Drop)
        zone.addEventListener("drop", (e) => {
            zone.classList.remove("border-primary", "bg-light");
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                // Validação básica de tipo
                if (file.type.startsWith("image/")) {
                    uploadImage(file, zone);
                } else {
                    alert("Por favor, selecione apenas ficheiros de imagem.");
                }
            }
        });
    });

    async function uploadImage(file, zone) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("object_id", zone.dataset.id);
        formData.append("app_label", zone.dataset.appLabel);
        formData.append("model_name", zone.dataset.modelName);

        const csrftoken = getCsrfToken();
        
        // Feedback de carregamento (Spinner)
        const originalContent = zone.innerHTML;
        zone.style.opacity = "0.7";
        zone.innerHTML = `
            <div class="d-flex align-items-center justify-content-center p-4 w-100">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                <span class="small fw-bold">A processar e redimensionar imagem...</span>
            </div>
        `;

        try {
            const response = await fetch(window.location.href, {
                method: "POST",
                headers: { "X-CSRFToken": csrftoken },
                body: formData,
            });

            // Se o status for 403 ou 500, o Django pode enviar HTML em vez de JSON
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const data = await response.json();
                if (response.ok) {
                    // Sucesso! Recarrega a página para mostrar a nova imagem na lista
                    window.location.reload();
                } else {
                    throw new Error(data.error || "Erro desconhecido no servidor");
                }
            } else {
                throw new Error("Resposta inválida do servidor (não é JSON)");
            }

        } catch (error) {
            console.error("Erro no upload:", error);
            alert("Erro ao enviar imagem: " + error.message);
            // Restaura o conteúdo original apenas em caso de erro
            zone.innerHTML = originalContent;
            zone.style.opacity = "1";
        }
    }
})();