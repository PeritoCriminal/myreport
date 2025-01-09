// myreportapp/static/js/image_editor1.js


export default class ImageEditor {
    constructor(someCanvasElement, maxSideVisibleCanvas = 800) {
        this.isTesting = false;
        this.canvas = someCanvasElement;
        this.maxSideVisibleCanvas = maxSideVisibleCanvas;
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.colorLine = 'red';
        this.realImage = new Image();
        this.realImageClient = { left: 0, top: 0, width: 800, height: 600, center_x: 400, center_y: 300 };
        this.realImageFactor = 2;
        this.mouseDownCoordinates = { x: 0, y: 0 };
        this.mouseMoveCoordinates = { x: 0, y: 0 };
        this.mouseUpCoordinates = { x: 0, y: 0 };
        this.lastMouseCoordinates = [];
        this.isMouseDown = false;
        this.isDragging = false;
        this.isZooming = false;
        this.isCropping = false;
        this.operation = 'Nenhuma operação ...';
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
    }

    handleMouseDown(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        this.mouseDownCoordinates.x = dx;
        this.mouseDownCoordinates.y = dy;
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
        }
    }

    handleMouseUp(event) {
        if(this.isCropping){
            const left = this.mouseDownCoordinates.x * this.realImageFactor;
            const top = this.mouseDownCoordinates.y * this.realImageFactor;
            const width = (event.offsetX - this.mouseDownCoordinates.x) * this.realImageFactor;
            const height = (event.offsetY - this.mouseDownCoordinates.y) * this.realImageFactor;
            this.realImageClient.left = left;
            this.realImageClient.top = top;
            this.realImageClient.width = width;
            this.realImageClient.height = height;
            this.adjustSizes();
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
        this.isCropping = false;
    }

    setCenterClient() {
        this.realImageClient.center_x = (this.realImageClient.width / 2) - this.realImageClient.left;
        this.realImageClient.center_y = (this.realImageClient.height / 2) - this.realImageClient.top;
    }

    selectImage() {
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
                    canvas.width = this.maxSideVisibleCanvas * this.realImageFactor;
                    canvas.height = canvas.width / ratio;
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    const compressedDataURL = canvas.toDataURL('image/jpeg', 0.9);
                    this.realImage = new Image();
                    this.realImage.src = compressedDataURL;
                    this.realImage.onload = () => {
                        this.realImageClient = { left: 0, top: 0, width: this.realImage.width, height: this.realImage.height, center_x: this.realImage.width / 2, center_y: this.realImage.height / 2 };
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
        const ratio = this.realImageClient.width / this.realImageClient.height;
        if (ratio > 1) {
            this.canvas.width = this.maxSideVisibleCanvas;
            this.canvas.height = this.canvas.width / ratio;
        } else {
            this.canvas.height = this.maxSideVisibleCanvas;
            this.canvas.width = this.canvas.height * ratio;
        }
        const imgX = Math.max(0, this.realImageClient.left);
        const imgY = Math.max(0, this.realImageClient.top);
        const clientW = Math.min(this.realImageClient.width, this.realImage.width - imgX);
        const clientH = Math.min(this.realImageClient.height, this.realImage.height - imgY);
        this.ctx.drawImage(
            this.realImage,
            imgX, imgY, clientW, clientH,
            0, 0, this.canvas.width, this.canvas.height
        );
        this.setCenterClient();
        if(this.isTesting){
            this.showRealImage();
            this.displayInfo();
        }
    }

    zoom() {
        let factor_zoom;
        if (this.lastMouseCoordinates[2].y < this.lastMouseCoordinates[1].y &&
            this.realImageClient.width >= this.realImage.width / 15) {
            factor_zoom = 0.98;
        } else if (this.lastMouseCoordinates[2].y > this.lastMouseCoordinates[1].y &&
            this.realImageClient.width >= this.realImage.width &&
            this.realImageClient.height >= this.realImage.height) {
            return;
        } else {
            factor_zoom = 1.02;
        }
        const newWidth = this.realImageClient.width * factor_zoom;
        const newHeight = this.realImageClient.height * factor_zoom;
        if (newWidth > this.realImage.width) {
            return;
        }
        if (newHeight > this.realImage.height) {
            return;
        }
        const centerX = this.realImageClient.left + this.realImageClient.width / 2;
        const centerY = this.realImageClient.top + this.realImageClient.height / 2;
        let newLeft, newTop;
        newLeft = centerX - newWidth / 2;
        if (newWidth + newLeft > this.realImage.width) {
            newLeft = this.realImage.width - newWidth;
        }
        newTop = centerY - newHeight / 2;
        if (newHeight + newTop > this.realImage.height) {
            newTop = this.realImage.height - newHeight;
        }
        if (newWidth >= this.realImage.width - 10) {
            newLeft = 0;
            this.realImageClient.width = this.realImage.width;
        }
        if (newHeight >= this.realImage.height - 10) {
            newTop = 0;
            this.realImageClient.height = this.realImage.height;
        }
        this.realImageClient.left = Math.max(0, newLeft);
        this.realImageClient.top = Math.max(0, newTop);
        this.realImageClient.width = newWidth;
        this.realImageClient.height = newHeight;
        this.operation = 'Aplicado zoom ...'
        this.adjustSizes();
    }

    pan() {
        const x_direction = this.lastMouseCoordinates[2].x - this.lastMouseCoordinates[0].x;
        const x_ratio = Math.abs(x_direction * (this.realImageClient.width / this.realImage.width));
        const y_direction = this.lastMouseCoordinates[2].y - this.lastMouseCoordinates[0].y;
        const y_ratio = Math.abs(y_direction * (this.realImageClient.height / this.realImage.height));
        const top = this.realImageClient.top;
        const left = this.realImageClient.left;
        const right = this.realImageClient.left + this.realImageClient.width;
        const botton = this.realImageClient.top + this.realImageClient.height;
        if (x_direction > 0) {
            if (left > 0) {
                this.realImageClient.left -= x_ratio;
            } else {
                this.realImageClient.left = 0;
            }
        } else {
            if (right < this.realImage.width) {
                this.realImageClient.left += x_ratio;
            } else {
                this.realImageClient.left = this.realImage.width - this.realImageClient.width;
            }
        }
        if (y_direction > 0) {
            if (top > 0) {
                this.realImageClient.top -= y_ratio;
            } else {
                this.realImageClient.top = 0;
            }
        } else {
            if (botton < this.realImage.height) {
                this.realImageClient.top += y_ratio
            } else {
                this.realImageClient.top = this.realImage.height - this.realImageClient.height;
            }
        }
        this.operation = 'Aplicado deslocamento (PAN) ...'
        this.adjustSizes();
    }

    crop() {
        const left = this.mouseDownCoordinates.x;
        const top = this.mouseDownCoordinates.y;
        const width = this.mouseMoveCoordinates.x - left;
        const height = this.mouseMoveCoordinates.y - top;
        this.ctx.setLineDash([10, 5]); 
        this.ctx.strokeStyle = this.colorLine; 
        this.ctx.lineWidth = 3; 
        this.ctx.beginPath(); 
        this.ctx.rect(left, top, width, height); 
        this.ctx.stroke();
        this.operation = 'Imagem recortada ...';
    }

    rotate(direction) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        let newLeft, newTop;
        if (direction === 1) {
            newLeft = this.realImage.height - (this.realImageClient.top + this.realImageClient.height);
            newTop = this.realImageClient.left;
        } else {
            newLeft = this.realImageClient.top;
            newTop = this.realImage.width - (this.realImageClient.left + this.realImageClient.width);
        }
        if (Math.abs(direction) % 2 !== 0) {
            canvas.width = this.realImage.height;
            canvas.height = this.realImage.width;
        } else {
            canvas.width = this.realImage.width;
            canvas.height = this.realImage.height;
        }
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate(direction * Math.PI / 2);
        ctx.drawImage(
            this.realImage,
            -this.realImage.width / 2,
            -this.realImage.height / 2
        );
        const rotatedImage = new Image();
        rotatedImage.src = canvas.toDataURL();
        rotatedImage.onload = () => {
            this.realImage = rotatedImage;
            this.realImageClient = {
                left: newLeft,
                top: newTop,
                width: this.realImageClient.height,
                height: this.realImageClient.width,
            };
            this.operation = 'Imagem rotacionada ...'
            this.adjustSizes();
        };
    }


    /******************************************************* */

    // TESTES
    displayInfo() {
        if(!this.isTesting)return;
        console.log('\n\n____________________________')
        console.log(this.operation);
        console.log(`Dimensões da imagem real: esquerda = ${this.realImage.left}, topo = ${this.realImage.top} largura = ${this.realImage.width}, altura = ${this.realImage.height}`);
        console.log(`Dimensões do frame: largura = ${this.realImageClient.width}, altura = ${this.realImageClient.height}`);
        console.log(`Posição do frame: esquerda = ${this.realImageClient.left}, topo = ${this.realImageClient.top}, centro = ${this.realImageClient.center_x} / ${this.realImageClient.center_y}`);
    }

    showRealImage() {
        if(!this.isTesting)return;
        const img = document.querySelector('#optimizedImage');
        img.src = this.realImage.src;
        this.realImage.top = this.maxSideVisibleCanvas + 30;
        this.divAboveImage(
            this.realImageClient.left,
            this.realImageClient.top,
            this.realImageClient.width,
            this.realImageClient.height
        );

    }

    divAboveImage(divLeft, divTop, divWidth, divHeight) {
        if(!this.isTesting)return;
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