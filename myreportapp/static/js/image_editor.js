export default class ImageEditor {
    constructor(someCanvasElement, maxSideVisibleCanvas = 800) {
        this.canvas = someCanvasElement;
        this.maxSideVisibleCanvas = maxSideVisibleCanvas;
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.realImage = new Image();
        this.realImageClient = { left: 0, top: 0, width: 800, height: 600 };
        this.realImageFactor = 2;

        this.lastCoordinates = [{x:0, y:0}, {x:0, y:0}, {x:0, y:0}];

        this.isMouseDown = false;
        this.isDragging = false;
        this.isZooming = false;
        this.isCropping = false;

        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
    }

    handleMouseDown(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        console.log(`botão do mouse abaixado em ${dx} / ${dy}.`)
        this.isMouseDown = true;
    }

    handleMouseMove(event) {
        if(!this.isMouseDown){
            return;
        }
        const dx = event.offsetX;
        const dy = event.offsetY;
        if(this.lastCoordinates.length > 2){
            this.lastCoordinates.shift();
        }
        this.lastCoordinates.push({x: dx, y: dy})
        console.log(`últimas coordenadas: ${this.lastCoordinates[0].x}/${this.lastCoordinates[0].y} - ${this.lastCoordinates[2].x}/${this.lastCoordinates[2].y}.`)
        if(this.isZooming){
            if(this.lastCoordinates[2].y < this.lastCoordinates[0].y){
                if(this.realImageClient.width > this.realImage.width/15){
                    this.zoom(0.98);
                };
            }else if(this.lastCoordinates[2].y > this.lastCoordinates[0].y){
                if(this.realImageClient.width < this.realImage.width){
                    this.zoom(1.02);
                };
            }else{
                return;
            }
        };

        if(this.isCropping){
            this.crop();
        }
        if(this.isDragging){
            this.pan();
        }
    }

    handleMouseUp(event){
        const dx = event.offsetX;
        const dy = event.offsetY;
        console.log(`botão do mouse levantado em ${dx} / ${dy}.`)
        this.clearOperations();
        this.adjustSizes();
    }

    clearOperations(){
        this.isMouseDown = false;
        this.isDragging = false;
        this.isZooming = false;
        this.isCropping = false;
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
                const img = new Image(); // Correção do new Image()
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
                        this.realImageClient = { left: 0, top: 0, width: this.realImage.width, height: this.realImage.height };
                        this.adjustSizes();
                        console.log('Orientação do canvas ajustada.');
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
    }


    adjustSizes() {
        const dx = 0;
        const dy = 0;
        const sx = this.realImageClient.left;
        const sy = this.realImageClient.top;
        const sWidth = this.realImageClient.width;
        const sHeight = this.realImageClient.height;
        const dWidth = this.realImage.width;
        const dHeight = this.realImage.height;
        const ratio = this.realImageClient.width / this.realImageClient.height;
        console.log(`-------------\nTamanho da imagem real: ${dx}:${dWidth} x ${dy}:${dHeight}`);
        console.log(`\nTamanho do recorte: ${sx}:${sWidth} x ${sy}:${sHeight}`);
        console.log(`\ntacha = ${ratio}\n---------------`)
        //console.log(`Bloquado para movimento e zoom: ${this.lockZoomAndPan()}`)
        if (ratio > 1) {
            this.canvas.width = this.maxSideVisibleCanvas;
            this.canvas.height = this.canvas.width / ratio;
        } else {
            this.canvas.height = this.maxSideVisibleCanvas;
            this.canvas.width = this.canvas.height * ratio;
        }
        this.ctx.drawImage(this.realImage, sx, sy, sWidth, sHeight, dx, dy, this.canvas.width, this.canvas.height);
        //this.ctx.drawImage(this.realImage, 0, 0, this.canvas.width, this.canvas.height);
        this.showRealImage();
    }

    rotate(direction) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = this.realImage.height;
        canvas.height = this.realImage.width;
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate(direction * Math.PI / 2);
        ctx.drawImage(
            this.realImage,
            -this.realImage.width / 2,
            -this.realImage.height / 2
        );
        const rotatedImage = new Image();
        rotatedImage.src = canvas.toDataURL();
        this.realImage = rotatedImage;
        this.realImage.onload = () => {
            this.realImageClient = { left: 0, top: 0, width: this.realImage.width, height: this.realImage.height };
            this.adjustSizes();
        };
    }

    zoom(factor) {
        console.log(`Aplicando Zoom ...`);
        const newWidth = this.realImageClient.width * factor;
        const newHeight = this.realImageClient.height * factor;
        const newLeft = (this.realImage.width - this.realImageClient.width) / 2;
        const newTop = (this.realImage.height - this.realImageClient.height) / 2;
        this.realImageClient.left = newLeft;
        this.realImageClient.top = newTop;
        this.realImageClient.width = newWidth;
        this.realImageClient.height = newHeight;
        this.adjustSizes();
    }

    crop(){
        console.log(`Recortando ... `)
    }

    pan() {
        console.log(`Arrastando ...`);
    }

    showRealImage() {
        const img = document.querySelector('#optimizedImage');
        img.src = this.realImage.src;
    }
}
