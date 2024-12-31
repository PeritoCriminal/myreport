// ImageEditor.js


export default class ImageEditor {
    constructor(canvasSelector, maxCanvasValue = 800) {
        this.canvas = document.querySelector(canvasSelector);
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.virtualCanvas = document.createElement('canvas');
        this.virtualCtx = this.virtualCanvas.getContext('2d', { willReadFrequently: true });
        this.factorCanvas = 4;
        this.maxCanvasValue = maxCanvasValue;
        this.aspectRatio = 1;
        this.zoom = 1;
        this.realImage = new Image();
        this.tempCanvas = document.createElement('canvas');
        this.tempCtx = this.tempCanvas.getContext('2d', { willReadFrequently: true });
        this.action = 0;
        this.actions = ['selecionar',
                        'rotacionar horário',
                        'rotacionar anti-horário',
                        'zoom',
                        'recortar',
                        ]
        this.listOfCanvasImages = [];
        this.logOfChanges = [];
    }


    // LISTA DE AÇÕES E DADOS EXIBIDOS DURANTE A FASE DE PROJETO.
    thisLogAction(){
        console.log(`\nAção: ${this.actions[this.action]}`);
        console.log(`Imagem Original ${this.realImage.width} x ${this.realImage.height}`);
        console.log(`Imagem no canvas: ${this.canvas.width} x ${this.canvas.height}`);
        console.log(`Imagem no canvas virutal: ${this.virtualCanvas.width} x ${this.virtualCanvas.height}`);
    }

    
    // AJUSTA AS DIMENSÕES DOS CANVAS, SE RETRATO OU PAISAGEM
    adjustSize(image){
        this.aspectRatio = image.width / image.height
        if(image.width > image.height){
            this.canvas.width = this.maxCanvasValue;
            this.canvas.height = this.maxCanvasValue / this.aspectRatio;
        }else{
            this.canvas.height = this.maxCanvasValue;
            this.canvas.width = this.maxCanvasValue * this.aspectRatio;
        }
        this.virtualCanvas.width = this.factorCanvas * this.canvas.width;
        this.virtualCanvas.height = this.factorCanvas * this.canvas.height;
        this.thisLogAction();
    }


    // SELECIONA UMA IMAGEM NO EXPLORADOR, EXIBE NO CANVAS E ATRIBUI AO CANVAS VIRTUAL
    selectImage() {
        const input = document.createElement('input');
        this.action = 0;
        input.type = 'file';
        input.accept = 'image/*';
        input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (e) => {
                this.realImage.src = e.target.result;    
                this.realImage.onload = () => {
                    this.adjustSize(this.realImage);
                    this.ctx.drawImage(
                        this.realImage,
                        0, 0,
                        this.canvas.width,
                        this.canvas.height
                    );
                    this.virtualCtx.drawImage(
                        this.realImage,
                        0, 0,
                        this.virtualCanvas.width,
                        this.virtualCanvas.height
                    );
                    this.listOfCanvasImages.push(this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height));
                    this.logOfChanges.push('Imagem carregada e ajustada.');
                };
            };
            reader.readAsDataURL(file);
        });
        input.click();
    }
    

    // ROTACIONA EM SENTIDO HORÁRIO
    rotateClockwise() {
        this.action = 1;
        this.tempCanvas.width = this.canvas.width;
        this.tempCanvas.height = this.canvas.height;
        this.tempCtx.drawImage(this.canvas, 0, 0);
        const newWidth = this.canvas.height;
        const newHeight = this.canvas.width;
        this.canvas.width = newWidth;
        this.canvas.height = newHeight;
        this.adjustSize(this.canvas);
        this.ctx.clearRect(0, 0, newWidth, newHeight);
        this.ctx.save();
        this.ctx.translate(newWidth / 2, newHeight / 2);
        this.ctx.rotate(Math.PI / 2); // Rotacionar 90 graus
        this.ctx.drawImage(this.tempCanvas, -this.tempCanvas.width / 2, -this.tempCanvas.height / 2);
        this.ctx.restore();
    }
    

    // ROTACIONA EM SENTIDO ANTI-HORÁRIO
    rotateCounterClockwise(){
        this.action = 2
        this.tempCanvas.width = this.canvas.width;
        this.tempCanvas.height = this.canvas.height;
        this.tempCtx.drawImage(this.canvas, 0, 0);
        const newWidth = this.canvas.height;
        const newHeight = this.canvas.width;
        this.canvas.width = newWidth;
        this.canvas.height = newHeight;
        this.adjustSize(this.canvas);
        this.ctx.clearRect(0, 0, newWidth, newHeight);
        this.ctx.save();
        this.ctx.translate(newWidth / 2, newHeight / 2);
        this.ctx.rotate(-Math.PI / 2); // Rotacionar 90 graus
        this.ctx.drawImage(this.tempCanvas, -this.tempCanvas.width / 2, -this.tempCanvas.height / 2);
        this.ctx.restore();
    }

    undo(){
        alert('desfazer');
    }

}
