export default class ImageEditor {
    constructor(someCanvasElement, maxSideVisibleCanvas = 800) {
        this.canvas = someCanvasElement;
        this.maxSideVisibleCanvas = maxSideVisibleCanvas;
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.realImage = new Image();
        this.realImageClient = { left: 0, top: 0, width: 800, height: 600, center_x: 400, center_y: 300 };
        this.realImageFactor = 2;

        this.lastCoordinates = [];

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
        console.log(`botão do mouse abaixado em ${dx} / ${dy}.`)
        this.lastCoordinates.length = 0;
        this.lastCoordinates.push({ x: dx, y: dy },{ x: dx, y: dy },{ x: dx, y: dy });
        this.isMouseDown = true;
    }

    handleMouseMove(event) {
        if (!this.isMouseDown) {
            return;
        }
        const dx = event.offsetX;
        const dy = event.offsetY;
        if (this.lastCoordinates.length > 2) {
            this.lastCoordinates.shift();
        }
        this.lastCoordinates.push({ x: dx, y: dy })
        //console.log(`últimas coordenadas: ${this.lastCoordinates[0].x}/${this.lastCoordinates[0].y} - ${this.lastCoordinates[2].x}/${this.lastCoordinates[2].y}.`)
        if (this.isZooming) {
            if (this.lastCoordinates[2].y < this.lastCoordinates[1].y) {
                if (this.realImageClient.width >= this.realImage.width / 15) {
                    this.zoom(0.98);
                };
            } else if (this.lastCoordinates[2].y > this.lastCoordinates[1].y) {
                if (this.realImageClient.width > this.realImage.width - 50 || this.realImageClient.height > this.realImage.height - 50) {
                    return;
                } else {
                    this.zoom(1.02);
                };
            } else {
                return;
            }
        };

        if (this.isDragging) {
                this.pan();
        };

        if (this.isCropping) {
            this.crop();
        }
        if (this.isDragging) {
            this.pan();
        }
    }

    handleMouseUp(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        console.log(`botão do mouse levantado em ${dx} / ${dy}.`)
        this.clearOperations();
        //this.adjustSizes();
    }

    handleMouseLeave(event) {
        const dx = event.offsetX;
        const dy = event.offsetY;
        console.log(`Saiu da área do canvas ... ${dx} / ${dy}.`)
        this.clearOperations();
        //this.adjustSizes();
    }

    clearOperations() {
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
                        this.realImageClient = { left: 0, top: 0, width: this.realImage.width, height: this.realImage.height, center_x: this.realImage.width / 2, center_y: this.realImage.height / 2 };
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

    getCenterClient(){
        this.realImageClient.center_x = (this.realImageClient.width / 2) - this.realImageClient.left;
        this.realImageClient.center_y = (this.realImageClient.height / 2) - this.realImageClient.top;
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
        const imgX = 0;
        const imgY = 0;
        const clientX = this.realImageClient.left;
        const clientY = this.realImageClient.top;
        const clientW = this.realImageClient.width;
        const clientH = this.realImageClient.height;
        const imgW = this.realImage.width;
        const imgH = this.realImage.height;
        console.log(`-------------\nTamanho da imagem real: x = ${imgX}, y = ${imgY}, W = ${imgW}, H = ${imgH}`);
        console.log(`\nTamanho do recorte: x = ${clientX}, y = ${clientY}, W = ${clientW}, H =${clientH}`);
        console.log(`\ntacha = ${ratio}\n---------------`)
        this.ctx.drawImage(this.realImage, clientX, clientY, clientW, clientH, imgX, imgY, this.canvas.width, this.canvas.height);
        this.showRealImage();
    }

    rotate(direction) {
        const canvas = document.createElement('canvas');
        canvas.width = this.realImage.width;
        canvas.height = this.realImage.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(this.realImage, 0, 0, this.realImage.width, this.realImage.height);
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate(direction * Math.PI / 2);
        const rotatedImage = new Image();
        rotatedImage.src = canvas.toDataURL();
        rotatedImage.onload = () =>{
            const parseSide = this.realImageClient.width;
            this.realImageClient.width = this.realImageClient.height;
            this.realImageClient.height = parseSide;
            // direction determina se é giro horário(1) ou anti-horário(-1).
            // na condição abaixo preciso das coordendas relativas para o ponto que será rotacionado juntamente com  canvas
            // esse ponto é definido pelo atributo this.realImageClient.center_x e y, que agora é rotacionado.
            if(direction = 1){
                const newRealImageClientCenter = {x:'?', y:'?'};
            }else{
                const newRealImageClientCenter = {x:'?', y:'?'};
                }
            this.realImageClient.left = newRealImageClientCenter.x - this.realImageClient.width / 2;
            this.realImageClient.top = newRealImageClientCenter.y - this.realImageClient.height / 2;
            this.setCenterClient(); // Esse método 
            this.adjustSizes();
        }
    }

    rotate1(direction) {
        const centerX = this.realImageClient.center_x;
        const centerY = this.realImageClient.center_y;
        console.log(`\n_____________centerX = ${centerX}, centerY = ${centerY}`)

        const rotatedImage = new Image();
        rotatedImage.src = canvas.toDataURL();
        this.realImage = rotatedImage;
    
        // Coordenadas relativas ao centro
        const relX = centerX - canvas.width / 2;
        const relY = centerY - canvas.height / 2;
    
        // Coordenadas após a rotação
        let newRelX, newRelY;
        if (direction === 1) { // Sentido horário
            newRelX = relY;
            newRelY = -relX;
        } else if (direction === -1) { // Sentido anti-horário
            newRelX = -relY;
            newRelY = relX;
        }
    
        // Ajustar de volta para o sistema original
        const newX = newRelX + canvas.width / 2;
        const newY = newRelY + canvas.height / 2;
    
        console.log(`New coordinates: (${newX}, ${newY})`);
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

    crop() {
        console.log(`Recortando ... `)
    }

    pan() {
        if(this.lastCoordinates.length<2){
            console.log(' sem pan ')
            return;
        }
        console.log('panngggggg')
        const x_direction = this.lastCoordinates[1].x - this.lastCoordinates[0].x;
        const x_ratio = Math.abs(x_direction * (this.realImageClient.width / this.realImage.width));
        const y_direction = this.lastCoordinates[1].y - this.lastCoordinates[0].y;
        const y_ratio = Math.abs(y_direction* (this.realImageClient.height / this.realImage.height));
        const top = this.realImageClient.top;
        const left = this.realImageClient.left;
        const right = this.realImageClient.left + this.realImageClient.width;
        const botton = this.realImageClient.top + this.realImageClient.height;
        console.log(`\n--------------\nleft: ${left}\ntop: ${top}\nright: ${right} x ${this.realImage.width}\nbotton:${botton} x ${this.realImage.height}\n------------`)
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

    showRealImage() {
        const img = document.querySelector('#optimizedImage');
        img.src = this.realImage.src;
    }
}
