// myreportapp/static/js/image_editor1.js

export default class ImageEditor {
    constructor(someCanvasElement) {
        this.isTesting = true;
        this.visibleCanvas = someCanvasElement;
        this.visibleCtx = this.visibleCanvas.getContext('2d');
        this.hideCanvas = document.createElement('canvas');
        this.hideCtx = this.hideCanvas.getContext('2d');
        this.clientArea = {left:0, top:0, width:300, height: 300}
        this.ratioOnLoadImage = 2;
        this.message = '';  

        if (this.isTesting) {
            this.hideCanvasDiv = document.createElement('div');
            document.body.appendChild(this.hideCanvasDiv);
            this.canvasClientArea = document.createElement('canvas');
            this.clientAreaCtx = this.canvasClientArea.getContext('2d');
            //this.hideCanvasDiv.appendChild(this.hideCanvas);
            this.hideCanvasDiv.appendChild(this.canvasClientArea);
            this.canvasClientArea.style.position = 'absolute';
            this.canvasClientArea.left = this.clientArea.left - 10;
            this.canvasClientArea.top = this.clientArea.top - 10;
            this.canvasClientArea.width = this.clientArea.width / 2;
            this.canvasClientArea.height = this.clientArea.height / 3;
            this.drawClientBorder();
        }        
    }

    selectImage() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (!file) {
                this.message = `Nenhuma imagem foi selecionada.\n`;
                console.warn(this.message);
                return;
            }
            if (!window.FileReader) {
                this.message = `Esse navegador não suporta o objeto FileReader. Não é possível selecionar e exibir a imagem.\n`;
                console.error(this.message);
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                const newImage = new Image();
                newImage.onload = () => {
                    this.message = `Imagem selecionada e exibida.\n`;
                    this.adjustVisibleCanvasSides(newImage, this.visibleCanvas);
                    this.visibleCtx.drawImage(newImage, 0, 0, this.visibleCanvas.width, this.visibleCanvas.height);
                    this.adjustVisibleCanvasSides(newImage, this.hideCanvas, this.ratioOnLoadImage);
                    this.hideCtx.drawImage(newImage, 0, 0, this.hideCanvas.width, this.hideCanvas.height);
                    this.adjustClientArea(0, 0, this.hideCanvas.width, this.hideCanvas.height);
                };
                newImage.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
        input.click();
    }

    adjustVisibleCanvasSides(imageElement, canvasElement, factor = 1) {
        if (!imageElement) {
            this.message = `Não foi possível ajustar as dimensões da imagem visível.`;
            console.warn(this.message);
            return;
        }
        const ratio = imageElement.width / imageElement.height;
        if (imageElement.height === 0 || imageElement.width === 0) {
            this.message = `Dimensões inválidas para a imagem.`;
            console.error(this.message);
            return;
        }
        canvasElement.left = 0
        canvasElement.top = 0;
        canvasElement.width = this.visibleCanvas.width;
        canvasElement.height = this.visibleCanvas.height;
        if (ratio >= 1) {
            canvasElement.width *= factor;
            canvasElement.height = canvasElement.width / ratio;
        } else {
            canvasElement.height *= factor;
            canvasElement.width = canvasElement * ratio;
        }

        if (this.isTesting) {
            this.message += `Dimensões ajustadas para imagem visível - left: ${canvasElement.left}, top: ${canvasElement.top}, width: ${canvasElement.width}, height: ${canvasElement.height}`;
            console.log(this.message);
        }
    }

    adjustClientArea(left, top, width, height) {
        this.clientArea.left = this.hideCanvas.left;
        this.clientArea.top = this.hideCanvas.top;
        this.clientArea.width = this.hideCanvas.width;
        this.clientArea.height = this.hideCanvas.height;
        
    
        if (this.isTesting) {
            this.message = `Área do recorte ajustada - left: ${left}px, top: ${top}px, width: ${width}px, height: ${height}px`;
            console.log(this.message);
        }
    }

    drawClientBorder(){
        this.clientAreaCtx.clearRect;
        this.clientAreaCtx.rect(this.canvasClientArea.left, this.clientArea.top, this.canvasClientArea.width, this.canvasClientArea.height);
        this.clientAreaCtx.stroke();
    }
    
    
}
