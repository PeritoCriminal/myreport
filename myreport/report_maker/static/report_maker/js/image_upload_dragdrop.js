/**
 * Módulo de upload via Arrastar e Soltar ou Botão "Colar".
 * A função de teclado (Ctrl+V) foi removida para evitar disparos acidentais.
 */
(function () {
    "use strict";

    function getCsrfToken() {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input && input.value) return input.value;
        return null;
    }

    const zones = document.querySelectorAll(".js-drag-drop-zone");

    zones.forEach((zone) => {
        // Drag & Drop
        ["dragenter", "dragover", "dragleave", "drop"].forEach((name) => {
            zone.addEventListener(name, (e) => { e.preventDefault(); e.stopPropagation(); });
        });

        zone.addEventListener("dragover", () => zone.classList.add("drag-over"));
        zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
        zone.addEventListener("drop", (e) => {
            zone.classList.remove("drag-over");
            handleFileSelection(e.dataTransfer.files, zone);
        });

        // Botão de Colar (Clipboard API)
        const pasteBtn = zone.querySelector(".js-paste-btn");
        if (pasteBtn) {
            pasteBtn.addEventListener("click", async (e) => {
                e.preventDefault();
                e.stopPropagation();

                try {
                    // Solicita permissão e lê os itens da área de transferência
                    const items = await navigator.clipboard.read();
                    const files = [];

                    for (const item of items) {
                        // Filtra apenas tipos de imagem
                        const imageTypes = item.types.filter(type => type.startsWith("image/"));
                        for (const type of imageTypes) {
                            const blob = await item.getType(type);
                            // Cria um ficheiro a partir do blob (o Django precisa de um nome de ficheiro)
                            const file = new File([blob], `colagem_${Date.now()}.png`, { type });
                            files.push(file);
                        }
                    }

                    if (files.length > 0) {
                        handleFileSelection(files, zone);
                    } else {
                        alert("Não foi encontrada nenhuma imagem na área de transferência.");
                    }
                } catch (err) {
                    console.error("Erro ao aceder ao clipboard:", err);
                    if (err.name === 'NotAllowedError') {
                        alert("Acesso negado. Por favor, permita que o site aceda à área de transferência nas definições do seu browser (clique no ícone do cadeado na barra de endereços).");
                    } else {
                        alert("Erro ao colar imagem. Verifique se copiou uma imagem (PrintScreen ou Copiar Imagem).");
                    }
                }
            });
        }
    });

    async function handleFileSelection(files, zone) {
        const imageFiles = Array.from(files).filter(f => f.type.startsWith("image/"));
        if (imageFiles.length === 0) return;

        const originalContent = zone.innerHTML;
        const total = imageFiles.length;

        try {
            for (let i = 0; i < total; i++) {
                updateZoneUI(zone, `A processar ${i + 1}/${total}...`);
                await uploadImage(imageFiles[i], zone);
            }
            window.location.reload();
        } catch (error) {
            console.error("Erro no processamento:", error);
            alert("Erro no upload: " + error.message);
            zone.innerHTML = originalContent;
        }
    }

    function updateZoneUI(zone, message) {
        zone.innerHTML = `
            <div class="d-flex align-items-center justify-content-center p-4 w-100 border border-primary bg-light rounded">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                <span class="small fw-bold">${message}</span>
            </div>
        `;
    }

    async function uploadImage(file, zone) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("object_id", zone.dataset.id);
        formData.append("app_label", zone.dataset.appLabel);
        formData.append("model_name", zone.dataset.modelName);

        const token = getCsrfToken();
        const response = await fetch(window.location.href, {
            method: "POST",
            headers: { "X-CSRFToken": token },
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erro ${response.status}: Verifique se o laudo está aberto para edição.`);
        }
    }
})();