// report_maker/static/report_maker/js/image_editor.js
//
// Editor simples (base) para o fragmento image_editor.html.
// - Renderiza a imagem no canvas responsivo (CSS 100% largura).
// - Mantém um "canvas de exportação" (offscreen) para preservar resolução.
// - Implementa ações: zoom in/out/reset, rotate left/right, crop (retângulo), blur (pintura simples), reset.
// - No submit, exporta PNG/JPEG via toBlob e injeta no input[type=file] do form.
//
// Ajuste solicitado:
// - Se for CREATE (sem data-initial-image-url): abrir automaticamente o seletor de arquivo ao iniciar.
// - Se for EDIT (com data-initial-image-url): carregar a imagem do BD no canvas e NÃO abrir o seletor.
//
// Observação: este JS é um esqueleto funcional. Você pode evoluir depois (pan, handles de crop, blur por path etc).

(() => {
  "use strict";

  // ────────────────────────────────────────────────────────────
  // Helpers
  // ────────────────────────────────────────────────────────────
  function clamp(v, min, max) {
    return Math.max(min, Math.min(max, v));
  }

  function getFilenameFromUrl(url) {
    try {
      const u = new URL(url, window.location.href);
      const last = u.pathname.split("/").pop() || "image";
      return last.includes(".") ? last : `${last}.jpg`;
    } catch {
      return "image.jpg";
    }
  }

  function fileFromBlob(blob, filename, mime) {
    return new File([blob], filename, { type: mime || blob.type || "image/png" });
  }

  function setFileInput(fileInput, file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = (e) => reject(e);
      // permitir carregar de URL do próprio site; se for cross-origin, canvas pode “taint”
      img.crossOrigin = "anonymous";
      img.src = src;
    });
  }

  function canvasToBlob(canvas, mime, quality) {
    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), mime, quality);
    });
  }

  // ────────────────────────────────────────────────────────────
  // Editor core
  // ────────────────────────────────────────────────────────────
  class ImageEditor {
    constructor(root) {
      this.root = root;

      // DOM
      this.stage = root.querySelector("[data-stage]");
      this.canvas = root.querySelector("[data-canvas]");
      this.ctx = this.canvas.getContext("2d");

      this.fileRow = root.querySelector("[data-file-row]");
      this.fileInput = root.querySelector('input[type="file"][name="image"]');
      this.captionInput = root.querySelector('[name="caption"]');
      this.indexInput = root.querySelector('[name="index"]'); // pode não existir mais

      // flags do template
      this.pageMode = (root.dataset.mode || root.getAttribute("data-mode") || "create").toLowerCase();
      this.initialUrl = root.dataset.initialImageUrl || root.getAttribute("data-initial-image-url") || null;

      // Estado da imagem
      this.img = null;
      this.imgFilename = null;

      // Transformações/edições
      this.zoom = 1.0; // zoom visual (para viewport)
      this.rotation = 0; // 0, 90, 180, 270
      this.crop = null; // {x,y,w,h} no espaço da imagem ORIGINAL (antes de rotação)
      this.mode = null; // "crop" | "blur" | null

      // Crop selection (na tela / canvas display)
      this.cropSelecting = false;
      this.cropA = null; // {x,y} display coords
      this.cropB = null;

      // Blur strokes em coords da IMAGEM (antes de rotação)
      this.blurStrokes = []; // [{points:[{x,y}], radius, strength}]
      this.blurIsDrawing = false;
      this.currentStroke = null;

      // Config de exportação
      this.exportMime = "image/jpeg";
      this.exportQuality = 0.92;

      // Offscreen para exportar em resolução
      this.exportCanvas = document.createElement("canvas");
      this.exportCtx = this.exportCanvas.getContext("2d");

      // Bindings
      this._onResize = this._onResize.bind(this);
      this._onPointerDown = this._onPointerDown.bind(this);
      this._onPointerMove = this._onPointerMove.bind(this);
      this._onPointerUp = this._onPointerUp.bind(this);
      this._onFormSubmit = this._onFormSubmit.bind(this);
      this._onActionClick = this._onActionClick.bind(this);

      // Init
      this._attach();
      this._bootstrapInitialImageOrOpenPicker();
      this._onResize();
    }

    _attach() {
      // actions toolbar
      this.root.querySelectorAll("[data-action]").forEach((btn) => {
        btn.addEventListener("click", this._onActionClick);
      });

      // file input
      if (this.fileInput) {
        this.fileInput.addEventListener("change", async () => {
          const file = this.fileInput.files?.[0];
          if (!file) return;

          const url = URL.createObjectURL(file);
          this.imgFilename = file.name || "upload.jpg";
          await this.setImageFromUrl(url, /*hideFileRow=*/false);
          // não revogar o url agora, porque img pode precisar
        });
      }

      // pointer interactions (crop/blur)
      this.canvas.addEventListener("pointerdown", this._onPointerDown);
      this.canvas.addEventListener("pointermove", this._onPointerMove);
      window.addEventListener("pointerup", this._onPointerUp);

      // resize
      window.addEventListener("resize", this._onResize);

      // submit
      const form = this.root.closest("form");
      if (form) form.addEventListener("submit", this._onFormSubmit);
    }

    _openFilePickerOnce() {
      if (!this.fileInput) return;
      if (this._pickerOpened) return;
      this._pickerOpened = true;

      // Evita abrir em navegação "voltar" (bfcache) e garante clique após render
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          try {
            this.fileInput.click();
          } catch {
            // ignore
          }
        });
      });
    }

    async _bootstrapInitialImageOrOpenPicker() {
      // EDIT: se tem url inicial, carrega e não abre picker
      if (this.initialUrl) {
        this.imgFilename = getFilenameFromUrl(this.initialUrl);
        await this.setImageFromUrl(this.initialUrl, /*hideFileRow=*/true);
        return;
      }

      // CREATE: se não tem url inicial, abre picker automaticamente
      if (this.pageMode === "create") {
        this._openFilePickerOnce();
      }
    }

    async setImageFromUrl(url, hideFileRow) {
      this.img = await loadImage(url);

      // se for update, pode ocultar a linha do input de arquivo (opcional)
      if (hideFileRow && this.fileRow) {
        this.fileRow.classList.add("d-none");
      }

      // reset edições
      this.zoom = 1.0;
      this.rotation = 0;
      this.crop = null;
      this.blurStrokes = [];
      this.mode = null;

      // prepara export canvas (mantém resolução “boa”)
      // escolha: manter dimensão original, mas limitar para não estourar.
      const maxSide = 2560; // ajuste: 1920/2560/4096 conforme seu alvo
      const scale = Math.min(1, maxSide / Math.max(this.img.naturalWidth, this.img.naturalHeight));

      this.baseW = Math.round(this.img.naturalWidth * scale);
      this.baseH = Math.round(this.img.naturalHeight * scale);

      this._render();
    }

    destroy() {
      window.removeEventListener("resize", this._onResize);
      window.removeEventListener("pointerup", this._onPointerUp);
    }

    _onResize() {
      // Canvas “display”: largura do stage (CSS)
      const rect = this.stage.getBoundingClientRect();
      const cssW = Math.max(1, Math.floor(rect.width));

      // Mantém aspect ratio aproximado para exibição (baseW/baseH), sem depender do tamanho real
      const aspect = (this.baseW && this.baseH) ? (this.baseW / this.baseH) : (4 / 3);
      const cssH = Math.max(240, Math.floor(cssW / aspect));

      // define o tamanho interno do canvas baseado no devicePixelRatio (melhor nitidez)
      const dpr = window.devicePixelRatio || 1;
      this.canvas.style.width = `${cssW}px`;
      this.canvas.style.height = `${cssH}px`;
      this.canvas.width = Math.floor(cssW * dpr);
      this.canvas.height = Math.floor(cssH * dpr);

      this._render();
    }

    _onActionClick(e) {
      const action = e.currentTarget.getAttribute("data-action");
      if (!action) return;

      switch (action) {
        case "zoom_in":
          this.zoom = clamp(this.zoom * 1.15, 0.2, 8);
          break;
        case "zoom_out":
          this.zoom = clamp(this.zoom / 1.15, 0.2, 8);
          break;
        case "zoom_reset":
          this.zoom = 1.0;
          break;

        case "rotate_left":
          this.rotation = (this.rotation + 270) % 360;
          break;
        case "rotate_right":
          this.rotation = (this.rotation + 90) % 360;
          break;

        case "crop_start":
          this.mode = "crop";
          this.cropSelecting = false;
          this.cropA = null;
          this.cropB = null;
          break;
        case "crop_apply":
          this._applyCropFromSelection();
          this.mode = null;
          this.cropSelecting = false;
          break;
        case "crop_cancel":
          this.crop = null;
          this.mode = null;
          this.cropSelecting = false;
          this.cropA = null;
          this.cropB = null;
          break;

        case "blur_toggle":
          this.mode = (this.mode === "blur") ? null : "blur";
          break;
        case "blur_clear":
          this.blurStrokes = [];
          this.mode = null;
          break;

        case "reset_all":
          this.zoom = 1.0;
          this.rotation = 0;
          this.crop = null;
          this.blurStrokes = [];
          this.mode = null;
          this.cropSelecting = false;
          this.cropA = null;
          this.cropB = null;
          break;

        case "save":
          // submit será tratado no form submit
          break;
      }

      this._render();
    }

    _canvasToStageCoords(evt) {
      const r = this.canvas.getBoundingClientRect();
      const x = (evt.clientX - r.left);
      const y = (evt.clientY - r.top);
      // coords CSS; vamos converter para coords internas pelo dpr na hora do desenho
      return { x, y };
    }

    _stageToCanvasInternal(p) {
      const r = this.canvas.getBoundingClientRect();
      const sx = this.canvas.width / Math.max(1, r.width);
      const sy = this.canvas.height / Math.max(1, r.height);
      return { x: p.x * sx, y: p.y * sy };
    }

    _onPointerDown(evt) {
      if (!this.img) return;

      if (this.mode === "crop") {
        this.cropSelecting = true;
        const p = this._canvasToStageCoords(evt);
        this.cropA = p;
        this.cropB = p;
        evt.preventDefault();
        this._render();
        return;
      }

      if (this.mode === "blur") {
        this.blurIsDrawing = true;
        const p = this._canvasToStageCoords(evt);
        const imgP = this._stagePointToImagePoint(p);
        this.currentStroke = { points: [imgP], radius: 18, strength: 0.35 };
        this.blurStrokes.push(this.currentStroke);
        evt.preventDefault();
        this._render();
        return;
      }
    }

    _onPointerMove(evt) {
      if (!this.img) return;

      if (this.mode === "crop" && this.cropSelecting) {
        this.cropB = this._canvasToStageCoords(evt);
        evt.preventDefault();
        this._render();
        return;
      }

      if (this.mode === "blur" && this.blurIsDrawing && this.currentStroke) {
        const p = this._canvasToStageCoords(evt);
        const imgP = this._stagePointToImagePoint(p);
        this.currentStroke.points.push(imgP);
        evt.preventDefault();
        this._render();
        return;
      }
    }

    _onPointerUp() {
      this.cropSelecting = false;
      this.blurIsDrawing = false;
      this.currentStroke = null;
    }

    _applyCropFromSelection() {
      if (!this.cropA || !this.cropB || !this.img) return;

      const a = this.cropA;
      const b = this.cropB;

      const x1 = Math.min(a.x, b.x);
      const y1 = Math.min(a.y, b.y);
      const x2 = Math.max(a.x, b.x);
      const y2 = Math.max(a.y, b.y);

      // Ignora seleções pequenas
      if ((x2 - x1) < 10 || (y2 - y1) < 10) return;

      // Converte retângulo de display → retângulo em coords da imagem (antes de rotação)
      const p1 = this._stagePointToImagePoint({ x: x1, y: y1 });
      const p2 = this._stagePointToImagePoint({ x: x2, y: y2 });

      const cx1 = clamp(Math.min(p1.x, p2.x), 0, this.baseW);
      const cy1 = clamp(Math.min(p1.y, p2.y), 0, this.baseH);
      const cx2 = clamp(Math.max(p1.x, p2.x), 0, this.baseW);
      const cy2 = clamp(Math.max(p1.y, p2.y), 0, this.baseH);

      this.crop = { x: cx1, y: cy1, w: Math.max(1, cx2 - cx1), h: Math.max(1, cy2 - cy1) };

      // limpa seleção visual
      this.cropA = null;
      this.cropB = null;
    }

    _stagePointToImagePoint(stageP) {
      // mapeamento aproximado: como desenhamos a imagem centralizada,
      // precisamos reproduzir a mesma matemática usada no render().
      // Retorna ponto no espaço "base" (baseW/baseH) ANTES de rotação e crop.

      const r = this.canvas.getBoundingClientRect();
      const p = this._stageToCanvasInternal(stageP);

      // parâmetros do viewport do canvas interno
      const cw = this.canvas.width;
      const ch = this.canvas.height;

      // área efetiva da imagem no canvas (viewport)
      const view = this._getViewportRect(cw, ch);
      // remove offset para obter coords no viewport
      const vx = (p.x - view.x);
      const vy = (p.y - view.y);

      // normaliza para [0..1] no viewport, depois escala para base dims "rotacionadas"
      const nx = vx / Math.max(1, view.w);
      const ny = vy / Math.max(1, view.h);

      // dims depois de rotação (apenas para mapear)
      const rot = this.rotation % 360;
      const rw = (rot === 90 || rot === 270) ? this.baseH : this.baseW;
      const rh = (rot === 90 || rot === 270) ? this.baseW : this.baseH;

      const rx = nx * rw;
      const ry = ny * rh;

      // desfaz rotação para voltar ao espaço base (baseW/baseH)
      return this._unrotatePoint(rx, ry, rw, rh, rot);
    }

    _unrotatePoint(x, y, rw, rh, rot) {
      // transforma ponto em espaço rotacionado → espaço base (0..baseW/0..baseH)
      // considerando rotação em torno do topo-esquerdo do retângulo com ajustes padrão.
      // (matemática para 0,90,180,270)
      switch (rot) {
        case 0:
          return { x, y };
        case 90:
          return { x: y, y: (rw - x) };
        case 180:
          return { x: (rw - x), y: (rh - y) };
        case 270:
          return { x: (rh - y), y: x };
        default:
          return { x, y };
      }
    }

    _getViewportRect(cw, ch) {
      // viewport onde a imagem é desenhada (centrada), considerando zoom e proporção
      // aqui usamos base dims rotacionadas
      const rot = this.rotation % 360;
      const iw = (rot === 90 || rot === 270) ? this.baseH : this.baseW;
      const ih = (rot === 90 || rot === 270) ? this.baseW : this.baseH;

      const scaleFit = Math.min(cw / iw, ch / ih);
      const scale = scaleFit * this.zoom;

      const w = iw * scale;
      const h = ih * scale;

      const x = (cw - w) / 2;
      const y = (ch - h) / 2;

      return { x, y, w, h, scale };
    }

    _render() {
      const ctx = this.ctx;
      const cw = this.canvas.width;
      const ch = this.canvas.height;

      ctx.clearRect(0, 0, cw, ch);

      // fundo neutro
      ctx.save();
      ctx.fillStyle = "#f8f9fa";
      ctx.fillRect(0, 0, cw, ch);
      ctx.restore();

      if (!this.img || !this.baseW || !this.baseH) {
        // placeholder
        ctx.save();
        ctx.fillStyle = "#6c757d";
        ctx.font = "14px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Selecione uma imagem para iniciar.", cw / 2, ch / 2);
        ctx.restore();
        return;
      }

      // desenha imagem no canvas de display (com rotação/crop/blur)
      this._drawToContext(ctx, cw, ch, /*forExport=*/false);

      // overlay crop selection
      if (this.mode === "crop" && this.cropA && this.cropB) {
        const a = this._stageToCanvasInternal(this.cropA);
        const b = this._stageToCanvasInternal(this.cropB);
        const x = Math.min(a.x, b.x);
        const y = Math.min(a.y, b.y);
        const w = Math.abs(a.x - b.x);
        const h = Math.abs(a.y - b.y);

        ctx.save();
        ctx.strokeStyle = "rgba(0,0,0,0.6)";
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        ctx.strokeRect(x, y, w, h);
        ctx.restore();
      }
    }

    _drawToContext(ctx, cw, ch, forExport) {
      // 1) prepara um canvas temporário com a imagem base redimensionada (baseW/baseH)
      //    (isso evita depender de img.naturalWidth e mantém pipeline estável)
      const baseCanvas = document.createElement("canvas");
      baseCanvas.width = this.baseW;
      baseCanvas.height = this.baseH;
      const bctx = baseCanvas.getContext("2d");
      bctx.drawImage(this.img, 0, 0, this.baseW, this.baseH);

      // 2) aplica blur strokes no baseCanvas
      if (this.blurStrokes.length) {
        bctx.save();

        const blurBuffer = document.createElement("canvas");
        blurBuffer.width = this.baseW;
        blurBuffer.height = this.baseH;
        const bb = blurBuffer.getContext("2d");

        bb.filter = "blur(10px)";
        bb.drawImage(baseCanvas, 0, 0);
        bb.filter = "none";

        const masked = document.createElement("canvas");
        masked.width = this.baseW;
        masked.height = this.baseH;
        const mk = masked.getContext("2d");

        mk.drawImage(blurBuffer, 0, 0);
        mk.globalCompositeOperation = "destination-in";

        const alphaMask = document.createElement("canvas");
        alphaMask.width = this.baseW;
        alphaMask.height = this.baseH;
        const am = alphaMask.getContext("2d");
        am.clearRect(0, 0, this.baseW, this.baseH);
        am.globalCompositeOperation = "source-over";
        am.strokeStyle = "rgba(255,255,255,1)";
        am.lineCap = "round";
        am.lineJoin = "round";

        for (const stroke of this.blurStrokes) {
          am.lineWidth = (stroke.radius || 18) * 2;
          am.beginPath();
          const pts = stroke.points || [];
          if (pts.length) {
            am.moveTo(pts[0].x, pts[0].y);
            for (let i = 1; i < pts.length; i++) am.lineTo(pts[i].x, pts[i].y);
          }
          am.stroke();
        }

        mk.drawImage(alphaMask, 0, 0);

        bctx.globalCompositeOperation = "source-over";
        bctx.drawImage(masked, 0, 0);

        bctx.restore();
      }

      // 3) aplica crop (no espaço base antes da rotação)
      let srcX = 0, srcY = 0, srcW = this.baseW, srcH = this.baseH;
      if (this.crop) {
        srcX = Math.round(this.crop.x);
        srcY = Math.round(this.crop.y);
        srcW = Math.round(this.crop.w);
        srcH = Math.round(this.crop.h);
      }

      // 4) cria canvas rotacionado
      const rot = this.rotation % 360;
      const rotCanvas = document.createElement("canvas");
      if (rot === 90 || rot === 270) {
        rotCanvas.width = srcH;
        rotCanvas.height = srcW;
      } else {
        rotCanvas.width = srcW;
        rotCanvas.height = srcH;
      }
      const rctx = rotCanvas.getContext("2d");

      rctx.save();
      if (rot === 0) {
        rctx.drawImage(baseCanvas, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
      } else if (rot === 90) {
        rctx.translate(rotCanvas.width, 0);
        rctx.rotate(Math.PI / 2);
        rctx.drawImage(baseCanvas, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
      } else if (rot === 180) {
        rctx.translate(rotCanvas.width, rotCanvas.height);
        rctx.rotate(Math.PI);
        rctx.drawImage(baseCanvas, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
      } else if (rot === 270) {
        rctx.translate(0, rotCanvas.height);
        rctx.rotate(-Math.PI / 2);
        rctx.drawImage(baseCanvas, srcX, srcY, srcW, srcH, 0, 0, srcW, srcH);
      }
      rctx.restore();

      // 5) desenha rotCanvas no ctx alvo
      if (forExport) {
        ctx.clearRect(0, 0, cw, ch);
        ctx.drawImage(rotCanvas, 0, 0, cw, ch);
      } else {
        const view = this._getViewportRect(cw, ch);
        ctx.save();
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";
        ctx.drawImage(rotCanvas, view.x, view.y, view.w, view.h);
        ctx.restore();
      }

      this._lastRenderedRotCanvas = rotCanvas;
    }

    async _onFormSubmit(evt) {
      // Se não tem imagem, segue fluxo normal (para permitir validações do Django)
      if (!this.img) return;

      // Se não tem file input, também segue
      if (!this.fileInput) return;

      evt.preventDefault();

      const src = this._lastRenderedRotCanvas;
      if (!src) {
        this._prepareExportCanvasFromState();
      } else {
        this.exportCanvas.width = src.width;
        this.exportCanvas.height = src.height;
        this.exportCtx.clearRect(0, 0, src.width, src.height);
        this.exportCtx.drawImage(src, 0, 0);
      }

      const blob = await canvasToBlob(this.exportCanvas, this.exportMime, this.exportQuality);
      if (!blob) {
        evt.target.submit();
        return;
      }

      const ext = (this.exportMime === "image/png") ? "png" : "jpg";
      const baseName = (this.imgFilename || "imagem").replace(/\.[^.]+$/, "");
      const outName = `${baseName}_edit.${ext}`;

      const file = fileFromBlob(blob, outName, this.exportMime);
      setFileInput(this.fileInput, file);

      evt.target.submit();
    }

    _prepareExportCanvasFromState() {
      const rot = this.rotation % 360;
      let w = this.baseW, h = this.baseH;
      if (this.crop) {
        w = Math.round(this.crop.w);
        h = Math.round(this.crop.h);
      }
      if (rot === 90 || rot === 270) {
        [w, h] = [h, w];
      }
      this.exportCanvas.width = w;
      this.exportCanvas.height = h;
      this._drawToContext(this.exportCtx, w, h, /*forExport=*/true);
    }
  }

  // ────────────────────────────────────────────────────────────
  // Boot
  // ────────────────────────────────────────────────────────────
  function initAll() {
    document.querySelectorAll("[data-editor]").forEach((root) => {
      // Evita inicializar duas vezes
      if (root.__imageEditor) return;
      root.__imageEditor = new ImageEditor(root);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }

  // opcional: expor para debug
  window.initImageEditors = initAll;
})();
