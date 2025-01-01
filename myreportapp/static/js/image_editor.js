export default class ImageEditor {
    constructor(canvasSelector, maxCanvasValue = 800) {
        this.canvas = document.querySelector(canvasSelector);
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.virtualCanvas = document.createElement('canvas');
        this.virtualCtx = this.virtualCanvas.getContext('2d', { willReadFrequently: true });
        this.factorCanvas = 2;
        this.sizeInMb = 0;
        this.maxCanvasValue = maxCanvasValue;
        this.maxHistory = 15;
        this.aspectRatio = 1;
        this.zoomLevel = 1;
        this.realImage = new Image();
        this.transitionImage = new Image();
        this.tempCanvas = document.createElement('canvas');
        this.tempCtx = this.tempCanvas.getContext('2d', { willReadFrequently: true });
        this.action = 0;
        this.actions = [
            'selecionar',
            'rotacionar horário',
            'rotacionar anti-horário',
            'zoom',
            'recortar'
        ];
        this.listOfCanvasImages = [];
        this.listOfVirtualCanvasImages = [];
        this.logOfChanges = [];
    }

    logAction() {
        const dataUrl = this.virtualCanvas.toDataURL();
        const base64Length = dataUrl.length - 'data:image/jpeg;base64,'.length;
        const sizeInBytes = (base64Length * 3) / 4;
        this.sizeInMb = sizeInBytes / (1024 * 1024);
        console.log(`\nAção: ${this.actions[this.action]}`);
        console.log(`Imagem Original ${this.realImage.width} x ${this.realImage.height}`);
        console.log(`Imagem no canvas: ${this.canvas.width} x ${this.canvas.height}`);
        console.log(`Imagem no canvas virtual: ${this.virtualCanvas.width} x ${this.virtualCanvas.height}`);
        console.log(`Tamanho em MB do arquivo de impressão: ${this.sizeInMb.toFixed(2)} MB`);
        console.log(`Histórico de ações: ${this.logOfChanges}`);
    }

    adjustSize(image) {
        this.aspectRatio = image.width / image.height;
        if (image.width > image.height) {
            this.canvas.width = this.maxCanvasValue;
            this.canvas.height = this.maxCanvasValue / this.aspectRatio;
        } else {
            this.canvas.height = this.maxCanvasValue;
            this.canvas.width = this.maxCanvasValue * this.aspectRatio;
        }
        this.virtualCanvas.width = this.factorCanvas * this.canvas.width;
        this.virtualCanvas.height = this.factorCanvas * this.canvas.height;
    }

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

                    this.ctx.drawImage(this.realImage, 0, 0, this.canvas.width, this.canvas.height);
                    this.virtualCtx.drawImage(this.realImage, 0, 0, this.virtualCanvas.width, this.virtualCanvas.height);

                    const reducedQualityImageURL = this.virtualCanvas.toDataURL('image/jpeg', 0.95);
                    const reducedQualityImage = new Image();
                    reducedQualityImage.src = reducedQualityImageURL;

                    reducedQualityImage.onload = () => {
                        this.virtualCtx.clearRect(0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
                        this.virtualCtx.drawImage(reducedQualityImage, 0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
                        this.saveState();
                        this.logAction();
                    };
                };
            };
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
        this.action = 1;
        this.rotate(this.canvas, this.ctx);
        this.rotate(this.virtualCanvas, this.virtualCtx);
        this.saveState();
        this.logAction();
    }

    rotateCounterClockwise() {
        this.action = 2;
        this.rotate(this.canvas, this.ctx, -1);
        this.rotate(this.virtualCanvas, this.virtualCtx, -1);
        this.saveState();
        this.logAction();
    }

    extractImage(canvas) {
        if (!(canvas instanceof HTMLCanvasElement)) {
            throw new Error("O parâmetro fornecido não é um canvas válido.");
        }
        const imageDataURL = canvas.toDataURL();
        const image = new Image();
        image.src = imageDataURL;
        return image;
    }
    
    // O código funciona quase perfeito, mas aplica um recorte nas imagens ao aplicar zoomIn, visto que
    // o usuário pode querer aplicar um zoomOut logo em seguida.
    zoom(factor) {
        // Atribuição da imagem do this.virtualCanvas porque a qualidade é melhor doque a do this.canvas.
        // transitionImage será aplicada primeiramente ao canvas virtual e depois ao canvas visível,
        // mantendo uma boa qualidade de impressão e visualização.
        this.transitionImage = this.extractImage(this.virtualCanvas);
        this.transitionImage.onload = () => {

            // Calcula as novas dimensões do canvas virtual
            let newWidth = this.virtualCanvas.width * factor;
            let newHeight = this.virtualCanvas.height * factor;    
            // Calcula os deslocamentos para centralizar
            let left = (newWidth - this.virtualCanvas.width) / 2;
            let top = (newHeight - this.virtualCanvas.height) / 2;    
            // Limpa o canvas
            this.virtualCtx.clearRect(0, 0, this.virtualCanvas.width, this.virtualCanvas.height);    
            // Redesenha a imagem no canvas com as novas dimensões
            // Mas aqui a imgem é recortada pelas arestas do canvas.
            // Dessa forma, ao aplicar zoomout após essa operação, a imagem ficará truncada.
            this.virtualCtx.drawImage(
                this.transitionImage, // Imagem a ser desenhada
                -left,                // Coordenada X de início
                -top,                 // Coordenada Y de início
                newWidth,             // Largura da imagem ajustada
                newHeight             // Altura da imagem ajustada
            );


            // Calcula as novas dimensões do canvas visivel
            // O objetivo é que todas as alterações feitas no canvas virtual sejam visiveis
            // ao usuário na canvas que aparece na tela.
            newWidth = this.canvas.width * factor;
            newHeight = this.canvas.height * factor;    
            // Calcula os deslocamentos para centralizar
            left = (newWidth - this.canvas.width) / 2;
            top = (newHeight - this.canvas.height) / 2;    
            // Limpa o canvas
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);    
            // Redesenha a imagem no canvas com as novas dimensões
            // mesmo problema do exposto acima no canvas virtual.
            this.ctx.drawImage(
                this.transitionImage, // Imagem a ser desenhada
                -left,                // Coordenada X de início
                -top,                 // Coordenada Y de início
                newWidth,             // Largura da imagem ajustada
                newHeight             // Altura da imagem ajustada
            );
    
            // Logs para depuração
            console.log(`Tamanho do canvas: ${this.canvas.width} x ${this.canvas.height}`);
            console.log(`Tamanho da imagem: ${this.transitionImage.width} x ${this.transitionImage.height}`); // Isso demonstra que a imgem está sendo recortada, o que não é esperado.
        };
    };
    
    
/*
    zoom1(factor) {
        this.zoomLevel += factor;
        if (this.zoomLevel < 0.1) this.zoomLevel = 0.1;
    
        const canvasWidth = this.canvas.width;
        const canvasHeight = this.canvas.height;
    
        const virtualWidth = this.virtualCanvas.width * this.zoomLevel;
        const virtualHeight = this.virtualCanvas.height * this.zoomLevel;
    
        // Calcula o deslocamento
        const offsetX = (virtualWidth - this.virtualCanvas.width) / 2;
        const offsetY = (virtualHeight - this.virtualCanvas.height) / 2;
    
        this.ctx.clearRect(0, 0, canvasWidth, canvasHeight);
        this.virtualCtx.clearRect(0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
    
        // Aplica o deslocamento ao desenhar na virtualCanvas
        this.virtualCtx.save();
        this.virtualCtx.translate(-offsetX, -offsetY);
        this.virtualCtx.scale(this.zoomLevel, this.zoomLevel);
        this.virtualCtx.drawImage(this.realImage, 0, 0);
        this.virtualCtx.restore();
    
        // Ajusta o deslocamento na canvas principal
        this.ctx.drawImage(this.virtualCanvas, 0, 0, canvasWidth, canvasHeight);
    
        this.logAction();
    }

*/
    zoomIn() {
        this.action = 3;
        this.zoom(0.1);
    }

    zoomOut() {
        const factor = -0.1;
        this.canvas.width *= factor;
        this.canvas.height *= factor;
        this.action = 4;
        this.zoom(factor);
    }

    saveState() {
        if (this.listOfCanvasImages.length >= this.maxHistory) {
            this.listOfCanvasImages.shift();
        }
        this.listOfCanvasImages.push(this.canvas.toDataURL('image/jpeg', 0.9));

        if (this.listOfVirtualCanvasImages.length >= this.maxHistory) {
            this.listOfVirtualCanvasImages.shift();
        }
        this.listOfVirtualCanvasImages.push(this.virtualCanvas.toDataURL('image/jpeg', 0.9));

        if (this.logOfChanges.length >= this.maxHistory) {
            this.logOfChanges.shift();
        }
        this.logOfChanges.push(this.action);
    }

    undo() {
        console.log('Função desfazer em desenvolvimento.');
    }
}
