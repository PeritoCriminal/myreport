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
        console.log(`Dimensões da imagem real: esquerda = ${this.realImage.left}, topo = ${this.realImage.top} largura = ${this.realImage.width}, altura = ${this.realImage.height}`);
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
        this.displayInfo();
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
                this.realImageClient.width > this.realImage.width ||
                this.realImageClient.height > this.realImage.height 
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
        const y_ratio = Math.abs(y_direction * (this.realImageClient.height / this.realImage.height));
        const top = this.realImageClient.top;
        const left = this.realImageClient.left;
        const right = this.realImageClient.left + this.realImageClient.width;
        const botton = this.realImageClient.top + this.realImageClient.height;
        if (x_direction > 0) {
            if (left > 0) {
                this.realImageClient.left -= x_ratio;
            } else {
                this.realImageClient.left = 0;
            }
        } else {
            if (right < this.realImage.width) {
                this.realImageClient.left += x_ratio;
            } else {
                this.realImageClient.left = this.realImage.width - this.realImageClient.width;
            }
        }
        if (y_direction > 0) {
            if (top > 0) {
                this.realImageClient.top -= y_ratio;
            } else {
                this.realImageClient.top = 0;
            }
        } else {
            if (botton < this.realImage.height) {
                this.realImageClient.top += y_ratio
            } else {
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
        let newLeft, newTop;
        if(direction === 1){
            newLeft = this.realImage.height - (this.realImageClient.top + this.realImageClient.height);
            newTop = this.realImageClient.left;
        }else{
            newLeft = this.realImageClient.top;
            newTop = this.realImage.width - (this.realImageClient.left + this.realImageClient.width);
        }
        if (Math.abs(direction) % 2 !== 0) {
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
            this.realImage = rotatedImage;
            this.realImageClient = {
                left: newLeft,
                top: newTop,
                width: this.realImageClient.height,
                height: this.realImageClient.width,
            };
            this.adjustSizes();
        };
    }  


    /******************************************************* */

    // TESTES
    showRealImage() {
        const img = document.querySelector('#optimizedImage');
        img.src = this.realImage.src;
        this.realImage.top = this.maxSideVisibleCanvas + 30;
        this.divAboveImage(
            this.realImageClient.left,
            this.realImageClient.top,
            this.realImageClient.width,
            this.realImageClient.height
            );
        
    }

    divAboveImage(divLeft, divTop, divWidth, divHeight) {
        const imgElement = document.getElementById('optimizedImage');
        const divElement = document.getElementById('overlayDiv');

        if (!divElement || !imgElement) {
            console.error("Elementos com os IDs fornecidos não foram encontrados.");
            return;
        }

        const imgLeft = 600;
        const imgTop = 1000;

        imgElement.style.position = "absolute";
        imgElement.style.left = `${imgLeft}px`;
        imgElement.style.top = `${imgTop}px`;
        //imgElement.style.width = `${imgWidth}px`;
        //imgElement.style.height = `${imgHeight}px`;

        const new_divLeft = imgLeft + divLeft;
        const new_divTop = imgTop + divTop;
        // Estilizar a div
        divElement.style.position = "absolute";
        divElement.style.left = `${new_divLeft}px`;
        divElement.style.top = `${new_divTop}px`;
        divElement.style.width = `${divWidth}px`;
        divElement.style.height = `${divHeight}px`;
        divElement.style.border = "2px solid red";
        divElement.style.backgroundColor = "transparent";
    }

}