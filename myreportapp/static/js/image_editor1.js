

export default class ImageEditor {
    constructor(canvasSelector, maxCanvasSideValue = 800) {
        this.maxCanvasSideValue = maxCanvasSideValue;
        this.canvas = document.querySelector(canvasSelector);
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.virtualCanvas = document.createElement('canvas');
        this.virtualCtx = this.virtualCanvas.getContext('2d', { willReadFrequently: true });
        this.tempCanvas = document.createElement('canvas');
        this.tempCtx = this.tempCanvas.getContext('2d', { willReadFrequently: true });
        this.factorCanvas = 2;
        this.currentScale = 1;
        this.mouseCoordinates = { x: 0, y: 0 };
        this.listCoordinates = [];
        this.mouseInitialPositionX = 0;
        this.mouseInitialPositionY = 0;
        this.mouseEndPositionX = 0;
        this.mouseEndPositionY = 0;
        this.maxHistory = 15;
        this.aspectRatio = 1;
        this.originalImage = new Image();
        this.transitionImage = new Image();
        this.isMouseDragging = false;
        //this.isZooming = false;
        this.isCropping = false;
        this.zoomInterval = null;
        this.listOfCanvasImages = [];
        this.listOfVirtualCanvasImages = [];
        this.isTesting = true;
        this.imgLeft = 0;
        this.imgTop = 0;
        this.imgWidth = 1;
        this.imgHeight = 1;
        this.imgCenter = {x: 1, y: 1}
    }

    setAspectRatio(canvasElement) {
        this.aspectRatio = canvasElement.width / canvasElement.height;
    }

    getCoordinates() {
        this.canvas.addEventListener('mousemove', (event) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouseCoordinates.x = event.clientX - rect.left;
            this.mouseCoordinates.y = event.clientY - rect.top;
        });
    }

    adjusteSizes(canvasElement) {
        this.setAspectRatio(canvasElement);
        if (this.aspectRatio < 1) {
            this.canvas.height = this.maxCanvasSideValue;
            this.canvas.width = this.aspectRatio * this.canvas.height
        } else {
            this.canvas.width = this.maxCanvasSideValue;
            this.canvas.height = this.canvas.width / this.aspectRatio;
        }
        this.virtualCanvas.width = this.canvas.width * this.factorCanvas;
        this.virtualCanvas.height = this.canvas.height * this.factorCanvas;
    }

    imgLimits(elementIMG, elementCanvas) {
        const scaledWidth = elementIMG.width * this.currentScale;
        const scaledHeight = elementIMG.height * this.currentScale;
        return scaledWidth <= elementCanvas.width && scaledHeight <= elementCanvas.height;
    }

    onMouseDown() {
        console.log('botão do mouse abaixado');
        this.isMouseDragging = true;
        this.getCoordinates;
        this.mouseInitialPositionX = this.mouseCoordinates.x;
        this.mouseInitialPositionY = this.mouseCoordinates.y;
    }

    onMouseUp() {
        this.clearOperations();
        console.log('botão do mouse levantado');
        this.getCoordinates;
        this.mouseEndPositionX = this.mouseCoordinates.x;
        this.mouseEndPositionY = this.mouseCoordinates.y;
    }

    onMouseMove() {
        if (!this.isMouseDragging) {
            console.log('Não arrastando.');
            return;
        }
        this.getCoordinates();
        console.log('arratando');
        //if (this.isZooming) {
        //    this.zoom();
        //}
        if (this.isCropping) {
            this.crop();
        }
        console.log(`Inicial: x = ${this.mouseInitialPositionX}, y = ${this.mouseInitialPositionY}\nFinal: x = ${this.mouseCoordinates.x}, y = ${this.mouseCoordinates.y}`)
    }

    clearOperations() {
        this.isMouseDragging = false;
        this.isCropping = false;
        //this.isZooming = false;
        console.log('Todoas as operação desabilitadas.')
    }

    selectImage() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (!file) {
                console.log('O arquivo escolhido não é um arquivo de imagem.')
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                this.originalImage.src = e.target.result;
                this.originalImage.onload = () => {
                    this.adjusteSizes(this.originalImage);
                    console.log('Aplicado adjustSise para imagem selecionada no explorador.');
                    this.virtualCtx.drawImage(this.originalImage, 0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
                    this.ctx.drawImage(this.originalImage, 0, 0, this.canvas.width, this.canvas.height);
                    const resucedQualityImageURL = this.virtualCanvas.toDataURL('image/jpeg', 0.95);
                    const reducedQualityImage = new Image();
                    reducedQualityImage.src = resucedQualityImageURL;
                    reducedQualityImage.onload = () => {
                        this.virtualCtx.clearRect(0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
                        this.virtualCtx.drawImage(reducedQualityImage, 0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
                        this.saveState();
                    }
                }
            }
            reader.readAsDataURL(file);
        });
        input.click();
    }

    rotate(canvas, ctx, direction = 1) {
        this.tempCanvas.width = canvas.width;
        this.tempCanvas.height = canvas.height;
        this.tempCtx.drawImage(canvas, 0, 0);

        const newWidth = canvas.height;
        const newHeight = canvas.width;
        canvas.width = newWidth;
        canvas.height = newHeight;

        ctx.clearRect(0, 0, newWidth, newHeight);
        ctx.save();
        ctx.translate(newWidth / 2, newHeight / 2);
        ctx.rotate(direction * Math.PI / 2);
        ctx.drawImage(this.tempCanvas, -this.tempCanvas.width / 2, -this.tempCanvas.height / 2);
        ctx.restore();
    }

    rotateClockwise() {
        this.rotate(this.canvas, this.ctx);
        this.rotate(this.virtualCanvas, this.virtualCtx);
        this.saveState();
    }

    rotateCounterClockwise() {
        this.rotate(this.canvas, this.ctx, -1);
        this.rotate(this.virtualCanvas, this.virtualCtx, -1);
        this.saveState();
    }

    zoom(factor = 1.2) {
        const factorZoom = factor;
        this.transitionImage.src = this.virtualCanvas.toDataURL('image/*jpeg', 0.95);
        this.transitionImage.onload = () =>{
            let newWidth = this.virtualCanvas.width * factorZoom;
            let newHeight = this.virtualCanvas.height * factorZoom;
            // Calcula os deslocamentos para centralizar
            let left = (newWidth - this.virtualCanvas.width) / 2;
            let top = (newHeight - this.virtualCanvas.height) / 2;
            // Limpa o canvas
            this.virtualCtx.clearRect(0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
            this.virtualCtx.drawImage(
                this.transitionImage, // Imagem a ser desenhada
                -left,                // Coordenada X de início
                -top,                 // Coordenada Y de início
                newWidth,             // Largura da imagem ajustada
                newHeight             // Altura da imagem ajustada
            );
            newWidth = this.canvas.width * factor;
            newHeight = this.canvas.height * factor;
            left = (newWidth - this.canvas.width) / 2;
            top = (newHeight - this.canvas.height) / 2;
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.drawImage(
                this.transitionImage, // Imagem a ser desenhada
                -left,                // Coordenada X de início
                -top,                 // Coordenada Y de início
                newWidth,             // Largura da imagem ajustada
                newHeight             // Altura da imagem ajustada
            );
            this.saveState();
        }
    }


    crop() {
        //Vou desenvolver depois.
        console.log('Aplicando crop.');
    }

    undo() {
        //Vou desenvolver depois .
        console.log('desfazer última operação.')
    }

    saveState() {
        if ((this.listOfCanvasImages.length >= this.maxHistory) || this.listOfVirtualCanvasImages.length >= this.maxHistory) {
            this.listOfCanvasImages.shift();
            this.listOfVirtualCanvasImages.shift();
        }
        this.listOfCanvasImages.push(this.canvas.toDataURL('image/jpeg', 0.9));
        this.listOfVirtualCanvasImages.push(this.virtualCanvas.toDataURL('image/jpeg', 0.9));
        console.log(`\nlistas de alterções: ${this.listOfCanvasImages.length} x ${this.listOfVirtualCanvasImages.length}.`)
        if (this.isTesting) {
            const imgElement = document.querySelector('#optimizedImage');
            this.showVirtualCanvas(imgElement);    // A imagem não é exibida como desejado        
        }
    }

    showVirtualCanvas(imgElement) {
        if (imgElement) {
            imgElement.src = this.virtualCanvas.toDataURL('image/jpeg', 0.9);
            console.log(`imgElement existe.`)
        } else {
            console.error("Elemento '#optimizedImage' não encontrado no DOM.");
        }
    }
}