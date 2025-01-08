//  Pfv, me ajude nas linhas comentadas no método rotate();


export default class ImageEditor {
    constructor(someCanvasElement, maxSideVisibleCanvas = 800) {
        this.canvas = someCanvasElement;
        this.maxSideVisibleCanvas = maxSideVisibleCanvas;
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.realImage = new Image();
        this.realImageClient = { left: 0, top: 0, width: 800, height: 600, center_x: 400, center_y: 300 };
        this.realImageFactor = 0.5;
        this.lastMouseCoordinates = [];
        this.isMouseDown = false;
        this.isDragging = false;
        this.isZooming = false;
        this.isCropping = false;
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
    }

    handleMouseDown(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        this.lastMouseCoordinates.length = 0;
        this.lastMouseCoordinates.push({ x: dx, y: dy }, { x: dx, y: dy }, { x: dx, y: dy });
        this.isMouseDown = true;
    }

    handleMouseMove(event) {
        if (!this.isMouseDown) {
            return;
        }
        const dx = event.offsetX;
        const dy = event.offsetY;
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
        const dx = event.offsetX;
        const dy = event.offsetY;
        this.clearOperations();
    }

    handleMouseLeave(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        this.clearOperations();
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

    displayInfo() {
        console.log('____________________________')
        console.log(`Dimensões da imagem real: largura = ${this.realImage.width}, altura = ${this.realImage.height}`);
        console.log(`Dimensões do frame: largura = ${this.realImageClient.width}, altura = ${this.realImageClient.height}`);
        console.log(`Posição do frame: esquerda = ${this.realImageClient.left}, topo = ${this.realImageClient.top}, centro = ${this.realImageClient.center_x} / ${this.realImageClient.center_y}`);
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
    
        // Constrain rendering to valid image dimensions
        const imgX = Math.max(0, this.realImageClient.left);
        const imgY = Math.max(0, this.realImageClient.top);
        const clientW = Math.min(this.realImageClient.width, this.realImage.width - imgX);
        const clientH = Math.min(this.realImageClient.height, this.realImage.height - imgY);
    
        console.log(`-------------\nTamanho da imagem real: x = ${imgX}, y = ${imgY}, W = ${clientW}, H = ${clientH}`);
        console.log(`\nTamanho do recorte: x = ${imgX}, y = ${imgY}, W = ${clientW}, H =${clientH}`);
        console.log(`\ntacha = ${ratio}\n---------------`);
    
        this.ctx.drawImage(
            this.realImage,
            imgX, imgY, clientW, clientH,
            0, 0, this.canvas.width, this.canvas.height
        );
        this.setCenterClient();
        this.showRealImage();
    }
    

    showRealImage() {
        const img = document.querySelector('#optimizedImage');
        img.src = this.realImage.src;
    }

    zoom() {
        console.log('zoom');
        let factor_zoom = 1;
    
        // Determine zoom in or out
        if (this.lastMouseCoordinates[2].y < this.lastMouseCoordinates[1].y) {
            if (this.realImageClient.width >= this.realImage.width / 15) {
                factor_zoom = 0.98; // Zoom out
            }
        } else if (this.lastMouseCoordinates[2].y > this.lastMouseCoordinates[1].y) {
            if (
                this.realImageClient.width > this.realImage.width - 50 ||
                this.realImageClient.height > this.realImage.height - 50
            ) {
                return;
            } else {
                factor_zoom = 1.02; // Zoom in
            }
        } else {
            return;
        }
    
        console.log('Aplicando Zoom ...');
    
        // Calculate new dimensions
        const newWidth = this.realImageClient.width * factor_zoom;
        const newHeight = this.realImageClient.height * factor_zoom;
    
        // Calculate new top-left position to maintain center
        const centerX = this.realImageClient.left + this.realImageClient.width / 2;
        const centerY = this.realImageClient.top + this.realImageClient.height / 2;
        const newLeft = centerX - newWidth / 2;
        const newTop = centerY - newHeight / 2;
    
        // Update realImageClient
        this.realImageClient.left = Math.max(0, newLeft); // Ensure it doesn't go outside bounds
        this.realImageClient.top = Math.max(0, newTop);
        this.realImageClient.width = newWidth;
        this.realImageClient.height = newHeight;
    
        // Adjust canvas rendering
        this.adjustSizes();
    }
    

    pan() {
        const x_direction = this.lastMouseCoordinates[2].x - this.lastMouseCoordinates[0].x;
        const x_ratio = Math.abs(x_direction * (this.realImageClient.width / this.realImage.width));
        const y_direction = this.lastMouseCoordinates[2].y - this.lastMouseCoordinates[0].y;
        const y_ratio = Math.abs(y_direction* (this.realImageClient.height / this.realImage.height));
        const top = this.realImageClient.top;
        const left = this.realImageClient.left;
        const right = this.realImageClient.left + this.realImageClient.width;
        const botton = this.realImageClient.top + this.realImageClient.height;

        if(x_direction > 0){
            if(left > 0){
                 this.realImageClient.left -= x_ratio;
            }else{
                this.realImageClient.left = 0;
            }
        }else{
            if(right < this.realImage.width){
                 this.realImageClient.left += x_ratio;
            }else{
                this.realImageClient.left = this.realImage.width - this.realImageClient.width;
            }
        }
        if(y_direction > 0){
            if (top > 0){
                this.realImageClient.top -= y_ratio;
            }else{
                this.realImageClient.top = 0;
            }
        }else{
            if(botton < this.realImage.height){
                this.realImageClient.top +=y_ratio
            }else{
                this.realImageClient.top = this.realImage.height - this.realImageClient.height;
            }
        }  
        this.adjustSizes();
    }


    crop() {
        console.log('crop');
    }

    rotate(direction) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (direction % 2 !== 0) {
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
            const cx0 = this.realImage.width / 2;
            const cy0 = this.realImage.height / 2;
            const cx1 = this.realImageClient.left + this.realImageClient.width / 2;
            const cy1 = this.realImageClient.top + this.realImageClient.height / 2;
            let cx2, cy2;
            if (direction === -1) { // Sentido horário
                cx2 = cx0 + (cy1 - cy0);
                cy2 = cy0 - (cx1 - cx0);
                console.log('---------- horário -------')
            } else if (direction === 1) { // Sentido anti-horário
                cx2 = cx0 - (cy1 - cy0);
                cy2 = cy0 + (cx1 - cx0);
                console.log('---------- anti-horário -------')
            } else {
                console.log('----------não aplicado cx2 e vy2 ----------')
                throw new Error("Direction deve ser 1 (horário) ou -1 (anti-horário).");
            }
            this.realImage = rotatedImage;
            this.realImageClient = { 
                left: cx2 - (this.realImageClient.width / 2), // é usado height porque realImageClient tb será rotacionado em 90°
                top: cy2 - (this.realImageClient.height / 2), // pelo memo totivo acima é usado width.
                height: this.realImageClient.width,
                width: this.realImageClient.height, 
            };
            this.adjustSizes();
        };
    }


    rotate1(direction) {
        // Cria um novo canvas temporário para manipular a rotação
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
    
        // Ajusta as dimensões do canvas para a rotação
        if (direction % 2 !== 0) { // Se a rotação for múltipla de 90 graus
            canvas.width = this.realImage.height; // Inverte as dimensões
            canvas.height = this.realImage.width;
        } else {
            canvas.width = this.realImage.width;
            canvas.height = this.realImage.height;
        }
    
        // Move a origem para o centro do novo canvas
        ctx.translate(canvas.width / 2, canvas.height / 2);
    
        // Converte a direção para radianos (90 graus por vez)
        const angle = direction * Math.PI / 2;
    
        // Aplica a rotação
        ctx.rotate(angle);
    
        // Desenha a imagem rotacionada
        ctx.drawImage(
            this.realImage,
            -this.realImage.width / 2,
            -this.realImage.height / 2
        );
    
        // Atualiza a imagem real com o novo conteúdo do canvas
        this.realImage = new Image();
        this.realImage.src = canvas.toDataURL();
    
        // Aguarda a nova imagem ser carregada para atualizar o cliente
        this.realImage.onload = () => {
            // Ajusta as dimensões da imagem no cliente
            if (direction % 2 !== 0) {
                // Troca largura e altura se a rotação for 90 ou 270 graus
                const temp = this.realImageClient.width;
                this.realImageClient.width = this.realImageClient.height;
                this.realImageClient.height = temp;
            }
    
            this.realImageClient.left = 0;
            this.realImageClient.top = 0;
    
            // Reajusta as dimensões da tela
            this.adjustSizes();
        };
    }
    
    
    
    


}