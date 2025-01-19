// myreportapp/static/js/image_editor1.js


export default class ImageEditor {
    constructor(someCanvasElement, maxSideVisibleCanvas = 800) {
        this.isTesting = true;
        this.visibleImage = someCanvasElement;
        this.maxSideVisibleCanvas = maxSideVisibleCanvas;
        this.ctx = this.visibleImage.getContext('2d', { willReadFrequently: true });
        this.colorLine = 'rgba(250, 0, 0, 1)';
        this.colorBackGround = 'rgba(250, 250, 0, 0.7)';
        this.textColor = 'rgba(0, 0, 0, 1)'
        this.lineThickness = 2;
        this.lastMarkNumber = 0;
        this.hideImage = new Image();
        this.hideImageClient = { left: 0, top: 0, width: 800, height: 600 };
        this.hideImageFactor = 2;
        this.mouseDownCoordinates = { x: 0, y: 0 };
        this.mouseMoveCoordinates = { x: 0, y: 0 };
        this.mouseUpCoordinates = { x: 0, y: 0 };
        this.lastMouseCoordinates = [];
        this.isMouseDown = false;
        this.isDragging = false;
        this.isZooming = false;
        this.isCropping = false;
        this.endCrop = false;
        this.initBlur = false;
        this.endBlur = false;
        this.isMarking = false;
        this.isLabeling = false;
        this.isPointing = false;
        this.isBlurring = false;
        this.endArrowTip = false;
        this.operation = 'Nenhuma operação ...';
        this.visibleImage.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.visibleImage.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.visibleImage.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.visibleImage.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
        this.savedImages = [];

        this.hideCanvas = document.createElement('canvas');
        this.hideCtx = this.hideCanvas.getContext('2d');
    }

    handleMouseDown(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        this.mouseDownCoordinates.x = dx;
        this.mouseDownCoordinates.y = dy;
        if (this.isMarking) {
            const idInputElement = document.querySelector('#numberInput');
            this.marker(idInputElement || null);
            return;
        }
        if (this.isLabeling) {
            const idInputElement = document.querySelector('#textInput');
            this.markerLabel(idInputElement || null);
            return;
        }
        if (this.isPointing) {
            this.endArrowTip = false;
        }
        if (this.isBlurring) {
            this.initBlur = true;
        }
        this.lastMouseCoordinates.length = 0;
        this.lastMouseCoordinates.push({ x: dx, y: dy }, { x: dx, y: dy }, { x: dx, y: dy });
        this.isMouseDown = true;
        this.operation = 'Botão esquerdo do mouse abaixado ...'
    }

    handleMouseMove(event) {
        if (!this.isMouseDown) {
            return;
        }
        const dx = event.offsetX;
        const dy = event.offsetY;
        this.mouseMoveCoordinates.x = dx;
        this.mouseMoveCoordinates.y = dy;
        this.lastMouseCoordinates.push({ x: dx, y: dy });
        if (this.lastMouseCoordinates.length > 2) {
            this.lastMouseCoordinates.shift();
        }
        switch (true) {
            case this.isZooming:
                this.zoom();
                break;
            case this.isCropping:
                this.crop();
                break;
            case this.isDragging:
                this.pan();
                break;
            case this.isPointing:
                this.pointTo();
                break;
            case this.isBlurring:
                this.blur();
                break;
        }
    }

    handleMouseUp(event) {
        if (this.isCropping) {
            this.endCrop = true;
            this.crop();
        }
        if (this.isBlurring) {
            this.endBlur = true;
            this.blur();
        }
        if (this.isPointing) {
            this.endArrowTip = true;
            this.pointTo();
        }
        this.clearOperations();
        this.operation = 'Botão esquerdo do mouse levantado ...'
    }

    handleMouseLeave(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        this.clearOperations();
        this.operation = 'Cursor do mouse saiu da área da imagem ...'
    }

    clearOperations() {
        this.isMouseDown = false;
        this.isDragging = false;
        this.isZooming = false;
        this.isMarking = false;
        this.isLabeling = false;
        this.endCrop = false;
        this.isPointing = false;
        this.isBlurring = false;
    }

    setCenterClient1() {
        this.hideImageClient.center_x = (this.hideImageClient.width / 2) - this.hideImageClient.left;
        this.hideImageClient.center_y = (this.hideImageClient.height / 2) - this.hideImageClient.top;
    }

    selectImage() {
        this.hideImageFactor = 2;
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (!file) {
                console.log('Nenhum arquivo foi escolhido ou o arquivo escolhido não é uma imagem.');
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const ratio = img.width / img.height;
                    canvas.width = this.maxSideVisibleCanvas * this.hideImageFactor;
                    canvas.height = canvas.width / ratio;
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    const compressedDataURL = canvas.toDataURL('image/jpeg', 0.9);
                    this.hideImage = new Image();
                    this.hideImage.src = compressedDataURL;
                    this.hideImage.onload = () => {
                        this.hideImageClient = { left: 0, top: 0, width: this.hideImage.width, height: this.hideImage.height, center_x: this.hideImage.width / 2, center_y: this.hideImage.height / 2 };
                        this.adjustSizes();
                    }
                };
                img.onerror = () => {
                    console.log('Erro ao carregar a imagem.');
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
        input.click();
        this.operation = 'Imagem selecionada e carregada ...'
    }

    adjustSizes() {
        if (this.hideImageFactor < 1) {
            this.visibleImage.width = this.hideImage.width;
            this.visibleImage.height = this.hideImage.height;
        }
        const ratio = this.hideImageClient.width / this.hideImageClient.height;
        if (ratio > 1) {
            this.visibleImage.width = this.maxSideVisibleCanvas;
            this.visibleImage.height = this.visibleImage.width / ratio;
        } else {
            this.visibleImage.height = this.maxSideVisibleCanvas;
            this.visibleImage.width = this.visibleImage.height * ratio;
        }
        const imgX = Math.max(0, this.hideImageClient.left);
        const imgY = Math.max(0, this.hideImageClient.top);
        const clientW = Math.min(this.hideImageClient.width, this.hideImage.width - imgX);
        const clientH = Math.min(this.hideImageClient.height, this.hideImage.height - imgY);
        this.ctx.drawImage(
            this.hideImage,
            imgX, imgY, clientW, clientH,
            0, 0, this.visibleImage.width, this.visibleImage.height
        );
        this.updateListOfSavedImages();
        //this.setCenterClient();
        if (this.isTesting) {
            this.showRealImage();
            //this.updateListOfSavedImages();
            this.displayInfo();
        }
    }

    zoom() {
        let factor_zoom;
        if (this.lastMouseCoordinates[2].y < this.lastMouseCoordinates[1].y &&
            this.hideImageClient.width >= this.hideImage.width / 15) {
            factor_zoom = 0.98;
        } else if (this.lastMouseCoordinates[2].y > this.lastMouseCoordinates[1].y &&
            this.hideImageClient.width >= this.hideImage.width &&
            this.hideImageClient.height >= this.hideImage.height) {
            return;
        } else {
            factor_zoom = 1.02;
        }
        const newWidth = this.hideImageClient.width * factor_zoom;
        const newHeight = this.hideImageClient.height * factor_zoom;
        if (newWidth > this.hideImage.width) {
            return;
        }
        if (newHeight > this.hideImage.height) {
            return;
        }
        const centerX = this.hideImageClient.left + this.hideImageClient.width / 2;
        const centerY = this.hideImageClient.top + this.hideImageClient.height / 2;
        let newLeft, newTop;
        newLeft = centerX - newWidth / 2;
        if (newWidth + newLeft > this.hideImage.width) {
            newLeft = this.hideImage.width - newWidth;
        }
        newTop = centerY - newHeight / 2;
        if (newHeight + newTop > this.hideImage.height) {
            newTop = this.hideImage.height - newHeight;
        }
        if (newWidth >= this.hideImage.width - 10) {
            newLeft = 0;
            this.hideImageClient.width = this.hideImage.width;
        }
        if (newHeight >= this.hideImage.height - 10) {
            newTop = 0;
            this.hideImageClient.height = this.hideImage.height;
        }
        this.hideImageClient.left = Math.max(0, newLeft);
        this.hideImageClient.top = Math.max(0, newTop);
        this.hideImageClient.width = newWidth;
        this.hideImageClient.height = newHeight;
        this.operation = 'Aplicado zoom ...'
        this.adjustSizes();
    }

    pan() {
        const x_direction = this.lastMouseCoordinates[2].x - this.lastMouseCoordinates[0].x;
        const x_ratio = Math.abs(x_direction * (this.hideImageClient.width / this.hideImage.width));
        const y_direction = this.lastMouseCoordinates[2].y - this.lastMouseCoordinates[0].y;
        const y_ratio = Math.abs(y_direction * (this.hideImageClient.height / this.hideImage.height));
        const top = this.hideImageClient.top;
        const left = this.hideImageClient.left;
        const right = this.hideImageClient.left + this.hideImageClient.width;
        const botton = this.hideImageClient.top + this.hideImageClient.height;
        if (x_direction > 0) {
            if (left > 0) {
                this.hideImageClient.left -= x_ratio;
            } else {
                this.hideImageClient.left = 0;
            }
        } else {
            if (right < this.hideImage.width) {
                this.hideImageClient.left += x_ratio;
            } else {
                this.hideImageClient.left = this.hideImage.width - this.hideImageClient.width;
            }
        }
        if (y_direction > 0) {
            if (top > 0) {
                this.hideImageClient.top -= y_ratio;
            } else {
                this.hideImageClient.top = 0;
            }
        } else {
            if (botton < this.hideImage.height) {
                this.hideImageClient.top += y_ratio
            } else {
                this.hideImageClient.top = this.hideImage.height - this.hideImageClient.height;
            }
        }
        this.operation = 'Aplicado deslocamento (PAN) ...'
        this.adjustSizes();
    }

    crop() {
        // Método para delimitar uma área no canvas, recortar e exibir a imagem recortada.
        // Esse método ainda precisa de ajustes quando executado várias vezes.
        // A posição left e top não são precisas após o segundo crop.
        // Por enquanto está funcional.
        let left, top, width, height;
        if (this.mouseDownCoordinates.x < this.mouseMoveCoordinates.x) {
            left = this.mouseDownCoordinates.x;
            width = this.mouseMoveCoordinates.x - left;
        } else {
            left = this.mouseMoveCoordinates.x;
            width = this.mouseDownCoordinates.x - left;
        }
        if (this.mouseDownCoordinates.y < this.mouseMoveCoordinates.y) {
            top = this.mouseDownCoordinates.y;
            height = this.mouseMoveCoordinates.y - top;
        } else {
            top = this.mouseMoveCoordinates.y;
            height = this.mouseDownCoordinates.y - top;
        }
        this.adjustSizes();
        this.ctx.setLineDash([10, 5]);
        this.ctx.strokeStyle = this.colorLine;
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.rect(left, top, width, height);
        this.ctx.stroke();
        this.operation = 'Imagem recortada ...';
        if (this.endCrop) {
            const factor = this.hideImageFactor / (this.hideImage.width / this.hideImageClient.width);
            const client_left = (left * factor + this.hideImageClient.left);
            const client_top = (top * factor + this.hideImageClient.top);
            const client_widt = width * factor;
            const client_height = height * factor;
            this.hideImageClient.left = client_left;
            this.hideImageClient.top = client_top;
            this.hideImageClient.width = client_widt;
            this.hideImageClient.height = client_height;
            this.adjustSizes();
            this.isCropping = false;
        }
    }

    rotate_image(direction) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        let newLeft, newTop, msg;
        if (direction === 1) {
            newLeft = this.hideImage.height - (this.hideImageClient.top + this.hideImageClient.height);
            newTop = this.hideImageClient.left;
            msg = 'imagem rotacionada no sentido horário ...'
        } else {
            newLeft = this.hideImageClient.top;
            newTop = this.hideImage.width - (this.hideImageClient.left + this.hideImageClient.width);
            msg = 'imagem rotacionada no sentido anti-horário ...'
        }
        if (Math.abs(direction) % 2 !== 0) {
            canvas.width = this.hideImage.height;
            canvas.height = this.hideImage.width;
        } else {
            canvas.width = this.hideImage.width;
            canvas.height = this.hideImage.height;
        }
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate(direction * Math.PI / 2);
        ctx.drawImage(
            this.hideImage,
            -this.hideImage.width / 2,
            -this.hideImage.height / 2
        );
        const rotatedImage = new Image();
        rotatedImage.src = canvas.toDataURL();
        rotatedImage.onload = () => {
            this.hideImage = rotatedImage;
            this.hideImageClient = {
                left: newLeft,
                top: newTop,
                width: this.hideImageClient.height,
                height: this.hideImageClient.width,
            };
            this.operation = msg;
            this.adjustSizes();
        };
    }

    marker(idInputElement = null) {
        if (!this.isMarking) {
            return;
        }
        this.updateMarkOnRealImage(0, 0, '', 0, '', 0, 0)
        this.lastMarkNumber += 1;
        if (idInputElement) {
            idInputElement.value = this.lastMarkNumber + 1;
        }
        const { x, y } = this.mouseDownCoordinates;
        const text = `${this.lastMarkNumber}`;
        const fontSize = 26;
        const font = 'Arial';
        const padding = 5;
        const radius = 5;

        // Definir estilo do texto
        this.ctx.font = `${fontSize}px ${font}`;
        this.ctx.textBaseline = 'top';
        this.ctx.fillStyle = this.textColor;

        // Medir o tamanho do texto
        const textMetrics = this.ctx.measureText(text);
        const textWidth = textMetrics.width;
        const textHeight = fontSize; // Aproximação do tamanho da altura do texto

        // Configurar o estilo do fundo
        const backgroundX = x - padding;
        const backgroundY = y - padding;
        const backgroundWidth = textWidth + 2 * padding;
        const backgroundHeight = textHeight + 2 * padding;

        // Desenhar o fundo com bordas arredondadas
        this.ctx.beginPath();
        this.ctx.moveTo(backgroundX + radius, backgroundY);
        this.ctx.arcTo(backgroundX + backgroundWidth, backgroundY, backgroundX + backgroundWidth, backgroundY + backgroundHeight, radius);
        this.ctx.arcTo(backgroundX + backgroundWidth, backgroundY + backgroundHeight, backgroundX, backgroundY + backgroundHeight, radius);
        this.ctx.arcTo(backgroundX, backgroundY + backgroundHeight, backgroundX, backgroundY, radius);
        this.ctx.arcTo(backgroundX, backgroundY, backgroundX + backgroundWidth, backgroundY, radius);
        this.ctx.closePath();

        // Preencher fundo amarelo
        this.ctx.fillStyle = this.colorBackGround;
        this.ctx.fill();

        // Desenhar borda vermelha
        this.ctx.strokeStyle = this.colorLine;
        this.ctx.lineWidth = this.lineThickness;
        this.ctx.stroke();

        // Desenhar o texto no centro do fundo
        this.ctx.fillStyle = this.textColor;
        this.ctx.fillText(text, x, y);

        // Atualizar a imagem real com o marcador
        this.updateMarkOnRealImage(x, y, text, fontSize, font, padding, radius);
    }


    markerLabel(idInputElement = null) {
        if (!this.isLabeling || idInputElement === null || idInputElement.value.trim() == '') {
            return;
        }
        const { x, y } = this.mouseDownCoordinates;
        const text = `${idInputElement.value}`;
        const fontSize = 26;
        const font = 'Arial';
        const padding = 5;
        const radius = 5;

        // Definir estilo do texto
        this.ctx.font = `${fontSize}px ${font}`;
        this.ctx.textBaseline = 'top';
        this.ctx.fillStyle = this.textColor;

        // Medir o tamanho do texto
        const textMetrics = this.ctx.measureText(text);
        const textWidth = textMetrics.width;
        const textHeight = fontSize; // Aproximação do tamanho da altura do texto

        // Configurar o estilo do fundo
        const backgroundX = x - padding;
        const backgroundY = y - padding;
        const backgroundWidth = textWidth + 2 * padding;
        const backgroundHeight = textHeight + 2 * padding;

        // Desenhar o fundo com bordas arredondadas
        this.ctx.beginPath();
        this.ctx.moveTo(backgroundX + radius, backgroundY);
        this.ctx.arcTo(backgroundX + backgroundWidth, backgroundY, backgroundX + backgroundWidth, backgroundY + backgroundHeight, radius);
        this.ctx.arcTo(backgroundX + backgroundWidth, backgroundY + backgroundHeight, backgroundX, backgroundY + backgroundHeight, radius);
        this.ctx.arcTo(backgroundX, backgroundY + backgroundHeight, backgroundX, backgroundY, radius);
        this.ctx.arcTo(backgroundX, backgroundY, backgroundX + backgroundWidth, backgroundY, radius);
        this.ctx.closePath();

        // Preencher fundo amarelo
        this.ctx.fillStyle = this.colorBackGround;
        this.ctx.fill();

        // Desenhar borda vermelha
        this.ctx.strokeStyle = this.colorLine;
        this.ctx.lineWidth = this.lineThickness;
        this.ctx.stroke();

        // Desenhar o texto no centro do fundo
        this.ctx.fillStyle = this.textColor;
        this.ctx.fillText(text, x, y);

        // Atualizar a imagem real com o marcador
        this.updateMarkOnRealImage(x, y, text, fontSize, font, padding, radius);
    }

    // Novo método para atualizar a realImage
    updateMarkOnRealImage(x, y, text, fontSize, font, padding, radius) {
        // Calcular as proporções entre canvas e realImage
        const scaleFactor = this.hideImageClient.width / this.visibleImage.width;

        // Ajustar as coordenadas considerando o deslocamento do realImageClient
        const adjustedX = (x * scaleFactor) + this.hideImageClient.left;
        const adjustedY = (y * scaleFactor) + this.hideImageClient.top;

        // Obter o contexto da realImage
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.hideImage.width;
        tempCanvas.height = this.hideImage.height;
        const realCtx = tempCanvas.getContext('2d');

        // Desenhar a imagem original
        realCtx.drawImage(this.hideImage, 0, 0);

        // Configurar estilo do texto
        realCtx.font = `${fontSize * scaleFactor}px ${font}`;
        realCtx.textBaseline = 'top';

        // Medir o tamanho do texto
        const textMetrics = realCtx.measureText(text);
        const textWidth = textMetrics.width;
        const textHeight = fontSize * scaleFactor;

        // Configurar o estilo do fundo
        const backgroundX = adjustedX - padding * scaleFactor;
        const backgroundY = adjustedY - padding * scaleFactor;
        const backgroundWidth = textWidth + 2 * padding * scaleFactor;
        const backgroundHeight = textHeight + 2 * padding * scaleFactor;

        // Desenhar o fundo com bordas arredondadas
        realCtx.beginPath();
        realCtx.moveTo(backgroundX + radius * scaleFactor, backgroundY);
        realCtx.arcTo(backgroundX + backgroundWidth, backgroundY, backgroundX + backgroundWidth, backgroundY + backgroundHeight, radius * scaleFactor);
        realCtx.arcTo(backgroundX + backgroundWidth, backgroundY + backgroundHeight, backgroundX, backgroundY + backgroundHeight, radius * scaleFactor);
        realCtx.arcTo(backgroundX, backgroundY + backgroundHeight, backgroundX, backgroundY, radius * scaleFactor);
        realCtx.arcTo(backgroundX, backgroundY, backgroundX + backgroundWidth, backgroundY, radius * scaleFactor);
        realCtx.closePath();

        // Preencher fundo amarelo
        realCtx.fillStyle = this.colorBackGround;
        realCtx.fill();

        // Desenhar borda vermelha
        realCtx.strokeStyle = this.colorLine;
        realCtx.lineWidth = 1 * scaleFactor;
        realCtx.stroke();

        // Desenhar o texto no centro do fundo
        realCtx.fillStyle = this.textColor;
        realCtx.fillText(text, adjustedX, adjustedY);

        // Atualizar realImage
        const newImage = new Image();
        newImage.src = tempCanvas.toDataURL();
        newImage.onload = () => {
            this.hideImage = newImage;
        }
    }

    pointTo() {
        if (!this.isPointing) {
            return;
        }
        const arrowBase = this.mouseDownCoordinates;
        const arrowTip = this.mouseMoveCoordinates;
        this.ctx.clearRect(0, 0, this.visibleImage.width, this.visibleImage.height);
        this.adjustSizes();
        this.ctx.strokeStyle = this.colorLine;
        this.ctx.lineWidth = this.lineThickness;
        const baseRadius = this.ctx.lineWidth * 0.7;
        this.ctx.fillStyle = this.colorLine;
        this.ctx.beginPath();
        this.ctx.arc(arrowBase.x, arrowBase.y, baseRadius, 0, 2 * Math.PI);
        this.ctx.fill();
        const headLength = 10;
        const dx = arrowTip.x - arrowBase.x;
        const dy = arrowTip.y - arrowBase.y;
        const angle = Math.atan2(dy, dx);
        this.ctx.beginPath();
        this.ctx.moveTo(arrowBase.x, arrowBase.y);
        this.ctx.lineTo(arrowTip.x, arrowTip.y);
        this.ctx.stroke();
        this.ctx.beginPath();
        this.ctx.moveTo(arrowTip.x, arrowTip.y);
        this.ctx.lineTo(
            arrowTip.x - headLength * Math.cos(angle - Math.PI / 6),
            arrowTip.y - headLength * Math.sin(angle - Math.PI / 6)
        );
        this.ctx.lineTo(
            arrowTip.x - headLength * Math.cos(angle + Math.PI / 6),
            arrowTip.y - headLength * Math.sin(angle + Math.PI / 6)
        );
        this.ctx.lineTo(arrowTip.x, arrowTip.y);
        this.ctx.closePath();
        this.ctx.fillStyle = this.colorLine;
        this.ctx.fill();
        console.log(`Seta de ${arrowBase.x} x ${arrowBase.y} até ${arrowTip.x} x ${arrowTip.y}`);
        if (this.endArrowTip) {
            this.updateArrowOnRealImage(arrowBase.x, arrowBase.y, arrowTip.x, arrowTip.y, this.ctx.lineWidth, headLength);
        }
    }

    updateArrowOnRealImage(xStart, yStart, xEnd, yEnd, lineWidth, arrowHeadSize) {
        // Calcular as proporções entre canvas e realImage
        const scaleFactor = this.hideImageClient.width / this.visibleImage.width;

        // Ajustar as coordenadas considerando o deslocamento do realImageClient
        const adjustedXStart = (xStart * scaleFactor) + this.hideImageClient.left;
        const adjustedYStart = (yStart * scaleFactor) + this.hideImageClient.top;
        const adjustedXEnd = (xEnd * scaleFactor) + this.hideImageClient.left;
        const adjustedYEnd = (yEnd * scaleFactor) + this.hideImageClient.top;

        // Obter o contexto da realImage
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.hideImage.width;
        tempCanvas.height = this.hideImage.height;
        const realCtx = tempCanvas.getContext('2d');

        // Desenhar a imagem original
        realCtx.drawImage(this.hideImage, 0, 0);

        // Configurar estilo da seta
        realCtx.strokeStyle = this.colorLine;
        realCtx.lineWidth = lineWidth * scaleFactor;

        // Desenhar o corpo da seta
        realCtx.beginPath();
        realCtx.moveTo(adjustedXStart, adjustedYStart);
        realCtx.lineTo(adjustedXEnd, adjustedYEnd);
        realCtx.stroke();

        // Calcular o ângulo da ponta da seta
        const dx = adjustedXEnd - adjustedXStart;
        const dy = adjustedYEnd - adjustedYStart;
        const angle = Math.atan2(dy, dx);

        // Desenhar a ponta da seta
        const scaledArrowHeadSize = arrowHeadSize * scaleFactor;
        realCtx.beginPath();
        realCtx.moveTo(adjustedXEnd, adjustedYEnd);
        realCtx.lineTo(
            adjustedXEnd - scaledArrowHeadSize * Math.cos(angle - Math.PI / 6),
            adjustedYEnd - scaledArrowHeadSize * Math.sin(angle - Math.PI / 6)
        );
        realCtx.lineTo(
            adjustedXEnd - scaledArrowHeadSize * Math.cos(angle + Math.PI / 6),
            adjustedYEnd - scaledArrowHeadSize * Math.sin(angle + Math.PI / 6)
        );
        realCtx.lineTo(adjustedXEnd, adjustedYEnd);
        realCtx.closePath();
        realCtx.fillStyle = this.colorLine;
        realCtx.fill();

        // Desenhar a base da seta (círculo)
        const baseRadius = (lineWidth * 0.6) * scaleFactor;
        realCtx.beginPath();
        realCtx.arc(adjustedXStart, adjustedYStart, baseRadius, 0, 2 * Math.PI);
        realCtx.fillStyle = this.colorLine;
        realCtx.fill();

        // Atualizar realImage
        const newImage = new Image();
        newImage.src = tempCanvas.toDataURL();
        newImage.onload = () => {
            this.hideImage = newImage;
        };

        console.log("\n\n---------------\nscaleFactor:", scaleFactor);
        console.log("Adjusted Start:", adjustedXStart, adjustedYStart);
        console.log("Adjusted End:", adjustedXEnd, adjustedYEnd);
        console.log("LineWidth:", lineWidth, "ArrowHeadSize:", arrowHeadSize);
    }


    apply() {
        // Verifica se this.hideImage é uma imagem válida
        if (!(this.hideImage instanceof HTMLImageElement)) {
            console.error("this.hideImage não é uma instância de HTMLImageElement.");
            return;
        }
        console.log('Início da função apply...');

        // Verifica se this.hideImageClient contém as propriedades necessárias
        if (!this.hideImageClient ||
            typeof this.hideImageClient.left !== 'number' ||
            typeof this.hideImageClient.top !== 'number' ||
            typeof this.hideImageClient.width !== 'number' ||
            typeof this.hideImageClient.height !== 'number') {
            console.error("this.hideImageClient está inválido ou incompleto.");
            return;
        }
        console.log('Primeiras condições satisfeitas...');

        // Cria um canvas com as dimensões do frame
        const canvas = document.createElement('canvas');
        canvas.width = this.hideImageClient.width;
        canvas.height = this.hideImageClient.height;

        // Obtém o contexto 2D do canvas
        const ctx = canvas.getContext('2d');

        try {
            // Desenha o conteúdo do frame no canvas
            ctx.drawImage(
                this.hideImage,                              // Imagem original
                this.hideImageClient.left,                  // Coordenada X inicial do frame
                this.hideImageClient.top,                   // Coordenada Y inicial do frame
                this.hideImageClient.width,                 // Largura do frame
                this.hideImageClient.height,                // Altura do frame
                0,                                          // Coordenada X no canvas
                0,                                          // Coordenada Y no canvas
                this.hideImageClient.width,                 // Largura no canvas
                this.hideImageClient.height                 // Altura no canvas
            );

            // Cria uma nova imagem a partir do canvas
            const image = new Image();
            image.src = canvas.toDataURL();

            // Ajusta o this.hideImage após a nova imagem carregar
            image.onload = () => {
                this.hideImage = image;
                this.hideImageClient.left = 0;
                this.hideImageClient.top = 0;
                this.adjustSizes(); // Ajusta tamanhos após a imagem carregar
                this.hideImageFactor = this.hideImageClient.width / this.visibleImage.width;
            };
        } catch (error) {
            console.error("Erro ao processar a imagem:", error);
        }
    }


    // Método para verificar e atualizar a lista de imagens salvas
    updateListOfSavedImages() {
        const newImageSrc = this.hideImage?.src;

        // Verifica se a imagem existe e se é diferente da última salva
        if (newImageSrc && newImageSrc !== this.savedImages[this.savedImages.length - 1]) {
            this.savedImages.push(newImageSrc);

            // Mantém no máximo 20 imagens na lista
            if (this.savedImages.length > 20) {
                this.savedImages.shift();
            }
            console.log('Atualizado lista de imagens....');
        }
    }


    undo() {
        if (this.savedImages.length <= 1) {
            console.log("Não há imagens anteriores...");
            return;
        }

        // Obtém a última imagem da lista
        this.savedImages.pop();
        const lastImageSrc = this.savedImages.pop();

        // Cria uma nova imagem com o último src
        const newImage = new Image();
        newImage.src = lastImageSrc;

        // Define a nova imagem como a atual (hideImage)
        newImage.onload = () => {
            this.hideImage = newImage;
            this.hideImageClient.width = this.hideImage.width;
            this.hideImageClient.height = this.hideImage.height;
            this.adjustSizes();
            console.log("Imagem revertida para a anterior.");
        };

        newImage.onerror = () => {
            console.error("Erro ao carregar a imagem anterior.");
        };
    }





    /******************************************************* */



    blur(sizeValue = 10) {
        if (!this.isBlurring) {
            return;
        }

        const { x, y } = this.mouseMoveCoordinates;
        const radius = Math.floor(sizeValue / 2);
        const ctx = this.ctx;
        const canvas = this.visibleImage;

        const startX = Math.max(0, x - radius);
        const startY = Math.max(0, y - radius);
        const width = Math.min(sizeValue, canvas.width - startX);
        const height = Math.min(sizeValue, canvas.height - startY);

        const imageData = ctx.getImageData(startX, startY, width, height);
        const { data, width: imgWidth, height: imgHeight } = imageData;

        const listOfDataBlur = []; // Para armazenar os pixels alterados

        // Aplicar desfoque e armazenar pixels alterados
        this.applyBlurToData(data, imgWidth, imgHeight);
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const a = data[i + 3];

            const pixelIndex = i / 4;
            const pixelX = startX * this.hideImageFactor + (pixelIndex % imgWidth) * this.hideImageFactor;
            const pixelY = startY * this.hideImageFactor + Math.floor(pixelIndex / imgWidth) * this.hideImageFactor;
        }

        // Atualizar o canvas visível
        ctx.putImageData(imageData, startX, startY);

        // Finalizar o desfoque ao soltar o botão
        if (this.endBlur) {
            this.ctx.save();
            const newImg = new Image();
            newImg.src = this.visibleImage.toDataURL();
            newImg.onload = () => {
                this.hideImage = newImg;
                this.hideImageClient.width = this.hideImage.width;
                this.hideImageClient.height = this.hideImage.height;
                this.apply();
            }
            this.endBlur = false;
        };

    }

    // Função para aplicar desfoque
    applyBlurToData(data, imgWidth, imgHeight) {
        for (let i = 0; i < imgHeight; i++) {
            for (let j = 0; j < imgWidth; j++) {
                const idx = (i * imgWidth + j) * 4; // Índice do pixel atual
                const neighbors = this.getNeighbors(data, j, i, imgWidth, imgHeight);
                const avgColor = this.calculateAverageColor(neighbors);

                // Atualizar as cores do pixel com a média
                data[idx] = avgColor.r; // Vermelho
                data[idx + 1] = avgColor.g; // Verde
                data[idx + 2] = avgColor.b; // Azul
            }
        }
    }


    getNeighbors(data, x, y, width, height) {
        const neighbors = [];
        const radius = 1; // Raio para calcular os vizinhos

        for (let dx = -radius; dx <= radius; dx++) {
            for (let dy = -radius; dy <= radius; dy++) {
                const nx = x + dx;
                const ny = y + dy;

                // Verificar se o vizinho está dentro dos limites
                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    const idx = (ny * width + nx) * 4;
                    neighbors.push({
                        r: data[idx],
                        g: data[idx + 1],
                        b: data[idx + 2],
                    });
                }
            }
        }

        return neighbors;
    }

    calculateAverageColor(neighbors) {
        let totalR = 0, totalG = 0, totalB = 0;

        neighbors.forEach(({ r, g, b }) => {
            totalR += r;
            totalG += g;
            totalB += b;
        });

        const count = neighbors.length;
        return {
            r: Math.floor(totalR / count),
            g: Math.floor(totalG / count),
            b: Math.floor(totalB / count),
        };
    }




    /******************************************************* */

    // TESTES
    displayInfo() {
        if (!this.isTesting) return;
        console.log('\n\n____________________________')
        console.log(this.operation);
        console.log(`Dimensões da imagem real: esquerda = ${this.hideImage.left}, topo = ${this.hideImage.top} largura = ${this.hideImage.width}, altura = ${this.hideImage.height}`);
        console.log(`Dimensões do frame: largura = ${this.hideImageClient.width}, altura = ${this.hideImageClient.height}`);
        console.log(`Posição do frame: esquerda = ${this.hideImageClient.left}, topo = ${this.hideImageClient.top}, centro = ${this.hideImageClient.center_x} / ${this.hideImageClient.center_y}`);
        console.log(`Quantidade de imagens salvas = ${this.savedImages.length}.`)
    }

    showRealImage() {
        if (!this.isTesting) return;
        const img = document.querySelector('#optimizedImage');
        img.src = this.hideImage.src;
        this.hideImage.top = this.maxSideVisibleCanvas + 30;
        this.hideImage.left = 0;
        this.divAboveImage(
            this.hideImageClient.left,
            this.hideImageClient.top,
            this.hideImageClient.width,
            this.hideImageClient.height
        );

    }

    divAboveImage(divLeft, divTop, divWidth, divHeight) {
        if (!this.isTesting) return;
        const imgElement = document.getElementById('optimizedImage');
        const divElement = document.getElementById('overlayDiv');
        if (!divElement || !imgElement) {
            console.error("Elementos com os IDs fornecidos não foram encontrados.");
            return;
        }
        const imgLeft = 600;
        const imgTop = 1000;
        imgElement.style.position = "absolute";
        imgElement.style.left = `${imgLeft}px`;
        imgElement.style.top = `${imgTop}px`;
        const new_divLeft = imgLeft + divLeft;
        const new_divTop = imgTop + divTop;
        divElement.style.position = "absolute";
        divElement.style.left = `${new_divLeft}px`;
        divElement.style.top = `${new_divTop}px`;
        divElement.style.width = `${divWidth}px`;
        divElement.style.height = `${divHeight}px`;
        divElement.style.border = "2px solid red";
        divElement.style.backgroundColor = "transparent";
    }


}