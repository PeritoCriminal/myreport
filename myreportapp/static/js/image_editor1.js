

export default class ImageEditor{
    constructor(canvasSelector, maxCanvasSideValue = 800){
        this.maxCanvasSideValue = maxCanvasSideValue;
        this.canvas = document.querySelector(canvasSelector);
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.virtualCanvas = document.createElement('canvas');
        this.virtualCtx = this.virtualCanvas.getContext('2d', { willReadFrequently: true });
        this.tempCanvas = document.createElement('canvas');
        this.tempCtx = this.tempCanvas.getContext('2d', { willReadFrequently: true });
        this.factorCanvas = 2;
        this.mouseInitialPositionX = 0;
        this.mouseInitialPositionY = 0;
        this.mouseEndPositionX = 0;
        this.mouseEndPositionY = 0;
        this.maxHistory = 15;
        this.aspectRatio = 1;
        this.originalImage = new Image();
        this.isMouseDragging = false;
        this.isZooming = false;
        this.isCropping = false; 
        this.listOfCanvasImages = [];
        this.listOfVirtualCanvasImages = [];
        this.isTesting = true;
    }

    setAspectRatio(canvasElement){
        this.aspectRatio = canvasElement.width / canvasElement.height;
    }

    adjusteSizes(canvasElement){
        this.setAspectRatio(canvasElement);
        if(this.aspectRatio < 1){
            this.canvas.height = this.maxCanvasSideValue;
            this.canvas.width = this.aspectRatio * this.canvas.height
        }else{
            this.canvas.width = this.maxCanvasSideValue;
            this.canvas.height = this.canvas.width / this.aspectRatio;
        }
        this.virtualCanvas.width = this.canvas.width * this.factorCanvas;
        this.virtualCanvas.height = this.canvas.height * this.factorCanvas;
    }

    onMouseDown(){
        console.log('botão do mouse abaixado');
        this.isMouseDragging = true;
    }

    onMouseUp(){
        console.log('botão do mouse levantado');
        this.isMouseDragging = false;
    }

    onMouseMove(){
        if(!this.isMouseDragging){
            console.log('Não arrastando.');
            return;
        }
        console.log('arratando');
        if(this.isZooming){
            this.zoom();
        }
        if(this.isCropping){
            this.crop();
        }
    }

    clearOperations(){
        this.isMouseDragging = false;
        this.isCropping = false;
        this.isZooming = false;
        console.log('Todoas as operação desabilitadas.')
    }

    selectImage(){
        const input = document.createElement('input');
        input.type='file';
        input.accept = 'image/*';
        input.addEventListener('change', (event)=>{
            const file = event.target.files[0];
            if(!file){
                console.log('O arquivo escolhido não é um arquivo de imagem.')
                return;
            }
            const reader = new FileReader();
            reader.onload = (e)=>{
                this.originalImage.src = e.target.result;
                this.originalImage.onload = () => {
                    this.adjusteSizes(this.originalImage);
                    console.log('Aplicado adjustSise para imagem selecionada no explorador.');
                    this.virtualCtx.drawImage(this.originalImage, 0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
                    this.ctx.drawImage(this.originalImage, 0, 0, this.canvas.width, this.canvas.height);
                    const resucedQualityImageURL = this.virtualCanvas.toDataURL('image/jpeg', 0.95);
                    const reducedQualityImage = new Image();
                    reducedQualityImage.src = resucedQualityImageURL;
                    reducedQualityImage.onload = () =>{
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

    zoom(){
        //Vou desenvolver depois.
        console.log('Aplicando zoom');
    }

    crop(){
        //Vou desenvolver depois.
        console.log('Aplicando crop.');
    }

    undo(){
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
        if(this.isTesting){
        const imgElement = document.querySelector('#optimizedImage');            
            this.showVirtualCanvas(imgElement);    // A imagem não é exibida como desejado        
        }
    }

    showVirtualCanvas(imgElement){
        if (imgElement) {
            imgElement.src = this.virtualCanvas.toDataURL('image/jpeg', 0.9);
            console.log(`imgElement existe.`)
        } else {
            console.error("Elemento '#optimizedImage' não encontrado no DOM.");
        }
    }
}