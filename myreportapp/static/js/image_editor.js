// ImageEditor.js


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
        this.listOfVirtualCanvasImages = [];
        this.logOfChanges = [];
    }


    // LISTA DE AÇÕES E DADOS EXIBIDOS DURANTE A FASE DE PROJETO.
    thisLogAction() {
        const dataUrl = this.virtualCanvas.toDataURL(); // Obtém a imagem otimizada
        const base64Length = dataUrl.length - 'data:image/jpeg;base64,'.length; // Exclui o prefixo
        const sizeInBytes = (base64Length * 3) / 4; // Converte de Base64 para bytes
        this.sizeInMb = sizeInBytes / (1024 * 1024); // Converte de bytes para MB
        console.log(`\nAção: ${this.actions[this.action]}`);
        console.log(`Imagem Original ${this.realImage.width} x ${this.realImage.height}`);
        console.log(`Imagem no canvas: ${this.canvas.width} x ${this.canvas.height}`);
        console.log(`Imagem no canvas virutal: ${this.virtualCanvas.width} x ${this.virtualCanvas.height}`);
        console.log(`Tamanho em Mb do arquivo de impressão: ${this.sizeInMb.toFixed(2)} MB`);
        console.log(`Lista de ações: ${this.logOfChanges}`)

    }


    // AJUSTA AS DIMENSÕES DOS CANVAS, SE RETRATO OU PAISAGEM
    adjustSize(image) {
        this.aspectRatio = image.width / image.height
        if (image.width > image.height) {
            this.canvas.width = this.maxCanvasValue;
            this.canvas.height = this.maxCanvasValue / this.aspectRatio;
        } else {
            this.canvas.height = this.maxCanvasValue;
            this.canvas.width = this.maxCanvasValue * this.aspectRatio;
        }
        this.virtualCanvas.width = this.factorCanvas * this.canvas.width;
        this.virtualCanvas.height = this.factorCanvas * this.canvas.height;
        //this.thisLogAction();
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

                    // Desenhar no canvas principal
                    this.ctx.drawImage(
                        this.realImage,
                        0, 0,
                        this.canvas.width,
                        this.canvas.height
                    );

                    // Desenhar no canvas virtual
                    this.virtualCtx.drawImage(
                        this.realImage,
                        0, 0,
                        this.virtualCanvas.width,
                        this.virtualCanvas.height
                    );

                    // Gerar URL da imagem com qualidade reduzida
                    const reducedQualityImageURL = this.virtualCanvas.toDataURL('image/jpeg', 0.95);

                    // Criar uma nova imagem para carregar a URL de qualidade reduzida
                    const reducedQualityImage = new Image();
                    reducedQualityImage.src = reducedQualityImageURL;

                    reducedQualityImage.onload = () => {
                        // Limpar o canvas virtual e desenhar a imagem otimizada
                        this.virtualCtx.clearRect(0, 0, this.virtualCanvas.width, this.virtualCanvas.height);
                        this.virtualCtx.drawImage(
                            reducedQualityImage,
                            0, 0,
                            this.virtualCanvas.width,
                            this.virtualCanvas.height
                        );
                        //this.thisLogAction();
                        //console.log(`Tamanho em Mb do arquivo de impressão: ${this.sizeInMb.toFixed(2)} MB`);                    // Salvar o estado inicial
                        this.saveState();
                        this.thisLogAction();
                    };
                };
            };
            reader.readAsDataURL(file);
        });
        input.click();
    }



    // ROTACIONA  A IMAGEM
    rotate(element_canvas, element_ctx, clock_direction = 1) {
        this.tempCanvas.width = element_canvas.width;
        this.tempCanvas.height = element_canvas.height;
        this.tempCtx.drawImage(element_canvas, 0, 0);    
        const newWidth = element_canvas.height;
        const newHeight = element_canvas.width;    
        element_canvas.width = newWidth;
        element_canvas.height = newHeight;    
        element_ctx.clearRect(0, 0, newWidth, newHeight);
        element_ctx.save();
        element_ctx.translate(newWidth / 2, newHeight / 2);
        element_ctx.rotate(clock_direction * Math.PI / 2); // 90 graus ou -90 graus
        element_ctx.drawImage(this.tempCanvas, -this.tempCanvas.width / 2, -this.tempCanvas.height / 2);
        element_ctx.restore();    
        //this.thisLogAction(); // Verificar estado do canvas
        console.log(`Tamanho em Mb do arquivo de impressão: ${this.sizeInMb.toFixed(2)} MB`);
    }
    

    // ROTACIONA EM SENTIDO HORÁRIO
    rotateClockwise() {
        this.action = 1;
        this.rotate(this.canvas, this.ctx);
        this.rotate(this.virtualCanvas, this.virtualCtx);
        this.saveState();
        this.thisLogAction();
    }
    

    // ROTAICONA EM SENTIDO ANTI-HORÁRIO
    rotateCounterClockwise() {
        this.action = 2;
        this.rotate(this.canvas, this.ctx, -1);
        this.rotate(this.virtualCanvas, this.virtualCtx, -1);
        this.saveState();
        this.thisLogAction();
    }
    

    // ACRESCENTA AS IMAGEMS DO CANVAS E DO VIRTUALCANVAS ÀS SUAS REPECTIVAS LISTAS
    saveState() {
        if (this.listOfCanvasImages.length >= this.maxHistory) {
            this.listOfCanvasImages.shift();
        }
        this.listOfCanvasImages.push(this.canvas.toDataURL('image/jpeg', 0.9));
        if (this.listOfVirtualCanvasImages.length >= this.maxHistory) {
            this.listOfVirtualCanvasImages.shift();
        }
        this.listOfVirtualCanvasImages.push(this.virtualCanvas.toDataURL('image/jpeg', 0.9));
        if (this.logOfChanges.length >= this.maxHistory){
            this.logOfChanges.shift();
        }
        this.logOfChanges.push(this.action);
        console.log(`Estado salvo: canvas principal e virtual (${this.listOfCanvasImages.length} estados armazenados).`);
    }


    // DESFAZ A ÚLTIMA OPERAÇÃO
    undo() {
        alert('desfazer');
        console.log(`Tamanho em Mb do arquivo de impressão: ${this.sizeInMb.toFixed(2)} MB`);
    }

}
