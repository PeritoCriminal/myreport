# postsapp/models/post_models.py


from django.db import models
from stdimage.models import StdImageField
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from accountsapp.models import CustomUserModel


class PostModel(models.Model):
    author = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField('Título', max_length=200, blank=True, default='Imagem')
    content = models.TextField()
    image = StdImageField(
        upload_to='posts/images/',
        null=True,
        blank=True,
        delete_orphans=True,  # Remove imagens não usadas
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.image:
            # Abrir a imagem atual
            img = Image.open(self.image)

            # Verificar se a largura da imagem é maior que 1200px
            if img.width > 1200:
                # Calcular a proporção para reduzir a largura
                new_height = int((1200 / img.width) * img.height)
                img = img.resize((1200, new_height), Image.Resampling.LANCZOS)

                # Salvar a imagem redimensionada em um buffer
                buffer = BytesIO()
                img_format = img.format if img.format else 'JPEG'  # Manter o formato original
                img.save(buffer, format=img_format, quality=85)  # Ajustar qualidade se necessário
                buffer.seek(0)

                # Substituir a imagem original pela redimensionada
                self.image.save(self.image.name, ContentFile(buffer.read()), save=False)
                buffer.close()
        super().save(*args, **kwargs)

    def __str__(self):
        updatedat = ''
        if self.author.username != self.created_at:
            updatedat = f' e atualizado em {self.updated_at}'
        return f'Criado por {self.author.username} em {self.created_at}{updatedat}.'
