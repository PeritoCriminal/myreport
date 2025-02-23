# postsapp/models/post_models.py


from django.db import models
from stdimage.models import StdImageField
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from accountsapp.models import CustomUserModel
from django.utils import timezone
# from .comments_models import CommentsModel

class PostModel(models.Model):
    author = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField('Título', max_length=200, blank=True, default='Imagem')
    content = models.TextField()
    image = StdImageField(
        upload_to='posts/images/',
        null=True,
        blank=True,
        delete_orphans=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # comments = models.ForeignKey(CommentsModel, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)


    def save(self, *args, **kwargs):
        # Importação local para evitar problemas de importação circular
        from postsapp.models.comments_models import CommentsModel  
        
        if self.image:
            # Abrir a imagem atual
            img = Image.open(self.image)

            # Converter RGBA para RGB se necessário
            if img.mode == 'RGBA':
                background = Image.new("RGB", img.size, (255, 255, 255))  # Fundo branco
                background.paste(img, mask=img.split()[3])  # Combina a transparência
                img = background

            # Verificar se a largura da imagem é maior que 1200px
            if img.width > 1200:
                # Calcular a proporção para reduzir a largura
                new_height = int((1200 / img.width) * img.height)
                img = img.resize((1200, new_height), Image.Resampling.LANCZOS)

            # Salvar a imagem tratada em um buffer
            buffer = BytesIO()
            img_format = img.format if img.format else 'JPEG'  # Manter o formato original
            img.save(buffer, format=img_format, quality=85)  # Ajustar qualidade se necessário
            buffer.seek(0)

            # Substituir a imagem original pela tratada
            self.image.save(self.image.name, ContentFile(buffer.read()), save=False)
            buffer.close()

        super().save(*args, **kwargs)


    def format_date_to_post(self, date_field):
        """
        Retorna a data no formato dd-mm-aa.
        Recebe como parâmetro 'created_at' ou 'updated_at'.
        """
        if isinstance(date_field, timezone.datetime):
            return date_field.strftime('%d-%m-%y')
        return None

    def __str__(self):
        updatedat = ''
        if self.created_at != self.updated_at:
            updatedat = f' e atualizado em {self.format_date_to_post(self.updated_at)}'
        return f'Criado por {self.author.username} em {self.format_date_to_post(self.created_at)}{updatedat}.'

    class Meta:
        ordering = ['-updated_at']

