/**
 * Módulo de upload via Arrastar e Soltar ou Botão "Colar".
 * Suporta múltiplos arquivos e fornece feedback visual de zona ativa.
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
        // Eventos de Drag & Drop
        ["dragenter", "dragover", "dragleave", "drop"].forEach((name) => {
            zone.addEventListener(name, (e) => { 
                e.preventDefault(); 
                e.stopPropagation(); 
            });
        });

        // Adiciona destaque visual ao sobrevoar a zona específica
        zone.addEventListener("dragover", () => {
            zone.classList.add("drag-over", "border-primary", "shadow-sm");
        });

        // Remove destaque ao sair ou soltar
        ["dragleave", "drop"].forEach((name) => {
            zone.addEventListener(name, () => {
                zone.classList.remove("drag-over", "border-primary", "shadow-sm");
            });
        });

        zone.addEventListener("drop", (e) => {
            handleFileSelection(e.dataTransfer.files, zone);
        });

        // Botão de Colar (Clipboard API)
        const pasteBtn = zone.querySelector(".js-paste-btn");
        if (pasteBtn) {
            pasteBtn.addEventListener("click", async (e) => {
                e.preventDefault();
                e.stopPropagation();

                try {
                    const items = await navigator.clipboard.read();
                    const files = [];

                    for (const item of items) {
                        const imageTypes = item.types.filter(type => type.startsWith("image/"));
                        for (const type of imageTypes) {
                            const blob = await item.getType(type);
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
                    const msg = err.name === 'NotAllowedError' 
                        ? "Acesso negado. Permita o acesso ao clipboard nas definições do browser." 
                        : "Erro ao colar imagem. Verifique o conteúdo copiado.";
                    alert(msg);
                }
            });
        }
    });

    /**
     * Processa a fila de arquivos selecionados.
     */
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

    /**
     * Atualiza o estado visual da zona durante o upload.
     */
    function updateZoneUI(zone, message) {
        zone.innerHTML = `
            <div class="d-flex align-items-center justify-content-center p-4 w-100 border border-primary rounded">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                <span class="small fw-bold text-primary">${message}</span>
            </div>
        `;
    }

    async function uploadImage(file, zone) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("object_id", zone.dataset.id);
        formData.append("app_label", zone.dataset.appLabel);
        formData.append("model_name", zone.dataset.modelName);

        const response = await fetch(window.location.href, {
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Erro ${response.status}: Verifique se o laudo está aberto para edição.`);
        }
    }
})();