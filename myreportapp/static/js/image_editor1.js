

export default class ImageEditor{
    constructor(canvasSelector, maxCanvasSideValue = 800){
        this.maxCanvasSideValue = maxCanvasSideValue;
        this.canvas = document.querySelector(canvasSelector);
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.virtualCanvas = document.createElement('canvas');
        this.virtualCtx = this.virtualCanvas.getContext('2d', { willReadFrequently: true });
        this.factorCanvas = 2;
        this.mouseInitialPositionX = 0;
        this.mouseInitialPositionY = 0;
        this.mouseEndPositionX = 0;
        this.mouseEndPositionY = 0;
        this.maxHistory = 15;
        this.aspectRatio = 1;
        this.originalImage = new Image();
        this.isDraggin = false;
        this.isZooming = false;
        this.isCropping = false; 
        this.listOfCanvasImages = [];
        this.listOfVirtualCanvasImages = [];
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
        this.isDraggin = true;
    }

    onMouseUp(){
        console.log('botão do mouse levantado');
        this.isDraggin = false;
    }

    onMouseMove(){
        if(this.isDraggin){
            console.log('Arrastando ...')
        }
    }

    clearOperations(){
        this.isCropping = false;
        this.isZooming = false;
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
                    }
                    this.saveState();
                }
            }
            reader.readAsDataURL(file);
        });
        input.click();
    }

    saveState() {
        if ((this.listOfCanvasImages.length >= this.maxHistory) || this.listOfVirtualCanvasImages.length >= this.maxHistory) {
            this.listOfCanvasImages.shift();
            this.listOfVirtualCanvasImages.shift();
        }
        this.listOfCanvasImages.push(this.canvas.toDataURL('image/jpeg', 0.9));
        this.listOfVirtualCanvasImages.push(this.virtualCanvas.toDataURL('image/jpeg', 0.9));
    }
}