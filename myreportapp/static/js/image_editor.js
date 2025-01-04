export default class ImageEditor {
    constructor(someCanvasElement, maxSideVisibleCanvas = 800) {
        this.canvas = someCanvasElement;
        this.maxSideVisibleCanvas = maxSideVisibleCanvas;
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        this.realImage = new Image();
        this.realImageClient = {left:0, top:0, width:800, height:600};
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
                    canvas.width = 2000;
                    canvas.height = canvas.width / ratio;
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    const compressedDataURL = canvas.toDataURL('image/jpeg', 0.9);
                    this.realImage = new Image();
                    this.realImage.src = compressedDataURL;
                    this.realImage.onload = () => {
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
        const ratio = this.realImage.width / this.realImage.height;
        if (this.realImage.width > this.realImage.height) {
            this.canvas.width = this.maxSideVisibleCanvas;
            this.canvas.height = this.canvas.width / ratio;
        } else {
            this.canvas.height = this.maxSideVisibleCanvas;
            this.canvas.width = this.canvas.height * ratio;
        }
        this.ctx.drawImage(this.realImage, 0, 0, this.canvas.width, this.canvas.height);
        //this.showRealImage();
    }

    showRealImage(){
        const img = document.querySelector('#optimizedImage');
        img.src = this.realImage.src;
    }
}
