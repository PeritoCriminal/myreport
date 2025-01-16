// myreportapp/static/js/image_editor1.js

export default class ImageEditor {
    constructor() {
        this.isTesting = true;
        this.visibleCanvas = document.createElement('canvas');
        this.hideCanvas = document.createElement('canvas');
        this.clientArea = { left: 0, top: 0, width: 10, height: 10 };
        this.pixelOnMouseDown = { x: 0, y: 0 };
        this.pixelOnMuseMove = { x: 0, y: 0 };
        this.sizeFactor = 2;
        this.operation = '';
    }

    createVisibleCanvas(someDivElement) {
        if (!(someDivElement instanceof HTMLDivElement)) {
            console.error('O elemento fornecido não é um <div>.');
            return;
        }
    
        someDivElement.appendChild(this.visibleCanvas);
    
        // Usando getBoundingClientRect() para pegar a largura e altura
        const rect = someDivElement.getBoundingClientRect();
        this.visibleCanvas.width = rect.width;
        this.visibleCanvas.height = rect.height;
    
        console.log('Largura do div:', rect.width);
        console.log('Altura do div:', rect.height);
    
        this.operation = this.strings('createVisibleCanvas');
        this.showDataLog();
    }
    

    adjustVisbleCanvasSides(imgElement) {
        const ratio = imgElement.width / imgElement.height;
        console.log(`\n\n${imgElement.width} x ${imgElement.height} / ${ratio}`);
        if (imgElement.width >= imgElement.heigh) {
            this.visibleCanvas.height = this.visibleCanvas.width / ratio;
        } else {
            this.visibleCanvas.width = this.visibleCanvas.height * ratio;
        }
        this.operation = this.strings('adjustVisbleCanvasSides');
        this.showDataLog();
    }

    adjustHideCanvasSides() {
        this.hideCanvas.width = this.visibleCanvas.width * this.sizeFactor;
        this.hideCanvas.height = this.visibleCanvas.height * this.sizeFactor;
        this.operation = this.strings('adjustHideCanvasSides');
        this.showDataLog();
    }

    adjustClientArea(left, top, width, height) {
        if (left < 0 || top < 0 || left + width > this.hideCanvas.width || top + height > this.hideCanvas.height) {
            this.operation = this.strings('adjustClientAreaFail');
            this.showDataLog();
            return;
        }
        this.clientArea = { left, top, width, height };
        this.operation = this.strings('adjustClientArea');
        this.showDataLog();
    }

    transposePixel(pixelOnVisibleCanvas = this.pixelOnMouseDown) {
        try {
            if (!this.visibleCanvas || !this.clientArea) {
                throw new Error('Os atributos "visibleCanvas" ou "clientArea" não estão definidos.');
            }
            if (typeof pixelOnVisibleCanvas !== 'object' || pixelOnVisibleCanvas === null) {
                throw new TypeError('O parâmetro "pixelOnVisibleCanvas" deve ser um objeto contendo coordenadas x e y.');
            }
            if (typeof pixelOnVisibleCanvas.x !== 'number' || typeof pixelOnVisibleCanvas.y !== 'number') {
                throw new TypeError('O objeto "pixelOnVisibleCanvas" deve conter propriedades numéricas "x" e "y".');
            }
            const ratio = this.visibleCanvas.width / this.clientArea.width;
            if (!isFinite(ratio) || ratio <= 0) {
                throw new Error('O valor calculado para "ratio" é inválido. Verifique as dimensões do canvas e da área do cliente.');
            }
            const pixelOnHideCanvas = { x: 0, y: 0 };
            pixelOnHideCanvas.x = pixelOnVisibleCanvas.x * ratio + this.clientArea.left;
            pixelOnHideCanvas.y = pixelOnVisibleCanvas.y * ratio + this.clientArea.top;
            this.operation = this.strings('transposePixel');
            this.showDataLog();
            return pixelOnHideCanvas;
        } catch (error) {
            const originPixel = { x: 0, y: 0 };
            this.operation = this.strings('transposePixelFail');
            console.error('Erro em transposePixel:', error.message);
            return originPixel;
        }
    }

    strings(key) {
        const operations = {
            createVisibleCanvas: 'Criada a área visível para edição de imagens.',
            adjustVisbleCanvasSides: `Ajustadas largura e altura da imagem visivel: ${this.visibleCanvas.width} x ${this.visibleCanvas.height}`,
            adjustHideCanvasSides: `Ajustadas largura e altura da imagem virtual em ${this.sizeFactor}.`,
            adjustClientAreaFail: 'Falha ao ajustar área de recorte clientArea',
            adjustClientArea: 'Ajustadas margens e dimensões do recorte clientArea',
            transposePixelFail: 'Ponto de origem setado em x = 0 e y = 0',
            transposePixel: `Coordenadas ajustadas.`,
            selectImageOnExplorerFail: 'Nenhuma imagem foi selecionada.'
        };
        return operations[key] || 'Operação desconhecida';
    }

    /** testes */
    showDataLog() {
        if (!this.isTesting) {
            return;
        }
        console.log(this.operation);
    }

    selectImageOnExplorer() {
        try {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.addEventListener('change', (event) => {
                const file = event.target.files[0];
                if (!file) {
                    console.warn('Nenhum arquivo foi selecionado.');
                    this.operation = 'selectImageOnExplorerFail';
                    return;
                }
                if (typeof FileReader === 'undefined') {
                    console.error('FileReader não é suportado neste navegador.');
                    return;
                }
                const reader = new FileReader();
                reader.onload = (e) => {
                    const newImage = new Image();
                    newImage.onload = () => {
                        try {
                            this.adjustVisbleCanvasSides(newImage);
                            this.adjustHideCanvasSides();
                            this.adjustClientArea(0, 0, this.hideCanvas.width, this.hideCanvas.height);
                            const hideCtx = this.hideCanvas.getContext('2d');
                            const visibleCtx = this.visibleCanvas.getContext('2d');
                            if (!hideCtx || !visibleCtx) {
                                throw new Error('Erro ao obter os contextos dos canvases.');
                            }
                            hideCtx.drawImage(newImage, 0, 0, this.hideCanvas.width, this.hideCanvas.height);
                            visibleCtx.drawImage(newImage, 0, 0, this.visibleCanvas.width, this.visibleCanvas.height);
                            console.log('Imagem otimizada gerada com qualidade de 90%.');
                        } catch (canvasError) {
                            console.error('Erro ao ajustar e renderizar a imagem:', canvasError.message);
                        }
                    };
                    newImage.onerror = () => {
                        console.error('Erro ao carregar a imagem. Verifique o formato do arquivo.');
                    };
                    newImage.src = e.target.result;
                };
                reader.onerror = () => {
                    console.error('Erro ao ler o arquivo. Verifique se ele é válido.');
                };
                reader.readAsDataURL(file);
            });
            input.click();
        } catch (error) {
            console.error('Erro em selectImageOnExplorer:', error.message);
        }
    }

}
