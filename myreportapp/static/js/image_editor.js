// ImageEditor.js


export default class ImageEditor {
    constructor(canvasSelector, maxCanvasValue = 800) {
        this.canvas = document.querySelector(canvasSelector);
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.maxCanvasValue = maxCanvasValue;
        this.aspectRatio = 1;
        this.realImage = new Image();
        this.listOfCanvasImages = [];
        this.listOfRealImages = [];
    }

    selectImage(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.realImage.onload = () => {
                this.aspectRatio = this.realImage.width / this.realImage.height;
                this.adjustCanvasSize();
                this.ctx.drawImage(this.realImage, 0, 0, this.canvas.width, this.canvas.height);
                this.saveState();
            };
            this.realImage.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    adjustCanvasSize() {
        if (this.realImage.width > this.realImage.height) {
            this.canvas.width = this.maxCanvasValue;
            this.canvas.height = this.maxCanvasValue / this.aspectRatio;
        } else {
            this.canvas.height = this.maxCanvasValue;
            this.canvas.width = this.maxCanvasValue * this.aspectRatio;
        }
    }

    saveState() {
        // Remove os estados mais antigos se o limite for atingido
        if (this.listOfCanvasImages.length >= 10) this.listOfCanvasImages.shift();
        if (this.listOfRealImages.length >= 10) this.listOfRealImages.shift();

        // Salva o estado atual do canvas como snapshot
        const canvasSnapshot = this.canvas.toDataURL();
        this.listOfCanvasImages.push(canvasSnapshot);

        // Atualiza o realImage para refletir o estado atual do canvas
        const realImageClone = new Image();
        realImageClone.src = canvasSnapshot; // Usa o snapshot do canvas como origem da realImage
        this.realImage = realImageClone;

        // Também armazena a realImage clonada na lista de estados
        this.listOfRealImages.push(realImageClone);
    }



    // ROTACIONA A IMAGEM NO SENTIDO HORÁRIO
    rotateClockwise() {
        this.saveState();
        console.log(`\nÍndice do canvas: ${this.listOfCanvasImages.length - 1} | Índice da Imagem: ${this.listOfRealImages.length - 1}`);
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        tempCanvas.width = this.canvas.width;
        tempCanvas.height = this.canvas.height;
        tempCtx.drawImage(this.canvas, 0, 0);
        const newWidth = this.canvas.height;
        const newHeight = this.canvas.width;
        this.canvas.width = newWidth;
        this.canvas.height = newHeight;
        this.ctx.clearRect(0, 0, newWidth, newHeight);
        this.ctx.save();
        this.ctx.translate(newWidth / 2, newHeight / 2);
        this.ctx.rotate(Math.PI / 2);
        this.ctx.drawImage(tempCanvas, -tempCanvas.width / 2, -tempCanvas.height / 2);
        this.ctx.restore();
    }

    // ROTACIONA A IMAGEM NO SENTIDO ANTI-HORÁRIO
    rotateCounterClockwise() {
        this.saveState();
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        tempCanvas.width = this.canvas.width;
        tempCanvas.height = this.canvas.height;
        tempCtx.drawImage(this.canvas, 0, 0);
        const newWidth = this.canvas.height;
        const newHeight = this.canvas.width;
        this.canvas.width = newWidth;
        this.canvas.height = newHeight;
        this.ctx.clearRect(0, 0, newWidth, newHeight);
        this.ctx.save();
        this.ctx.translate(newWidth / 2, newHeight / 2);
        this.ctx.rotate(-Math.PI / 2);
        this.ctx.drawImage(tempCanvas, -tempCanvas.width / 2, -tempCanvas.height / 2);
        this.ctx.restore();
    }

    undo() {        
        if (this.listOfCanvasImages.length > 0) {
            // Restaura o estado anterior
            const previousCanvasImage = this.listOfCanvasImages[this.listOfCanvasImages.length - 1];
            const previousRealImage = this.listOfRealImages[this.listOfRealImages.length - 1];

            this.listOfCanvasImages.pop();
            this.listOfRealImages.pop();

            console.log(`\nÍndice do canvas: ${this.listOfCanvasImages.length - 1} | Índice da Imagem: ${this.listOfRealImages.length - 1}`);
            console.log(`Imagem real - largura: ${this.realImage.width}, altura: ${this.realImage.height}.`);

            // Atualiza a realImage com a anterior
            this.realImage.src = previousRealImage.src;
            this.realImage.onload = () => {
                // Ajusta o tamanho do canvas
                this.aspectRatio = this.realImage.width / this.realImage.height;
                this.adjustCanvasSize();

                // Desenha a imagem do canvas salvo
                const tempImage = new Image();
                tempImage.onload = () => {
                    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                    this.ctx.drawImage(tempImage, 0, 0, this.canvas.width, this.canvas.height);
                };
                tempImage.src = previousCanvasImage;
            };
        } else {
            // Limpa o canvas se não houver mais estados para restaurar
            alert('Não há mais ações a desfazer.');
        }        
    }

}
