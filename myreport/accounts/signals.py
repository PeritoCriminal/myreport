# accounts/signals.py
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
import os

from .models import User


def _delete_file_and_dirs(fieldfile):
    """
    Apaga o arquivo e remove diretórios vazios acima dele
    (profile/ , background/ e o diretório do UUID).
    """
    if not fieldfile or not fieldfile.name:
        return

    storage = fieldfile.storage
    name = fieldfile.name

    # Apaga o arquivo
    if storage.exists(name):
        storage.delete(name)

    # Caminho absoluto no disco
    abs_path = os.path.join(settings.MEDIA_ROOT, name)

    # Sobe removendo pastas vazias
    current_dir = os.path.dirname(abs_path)

    # Para quando chegar no MEDIA_ROOT
    media_root = os.path.abspath(settings.MEDIA_ROOT)

    while current_dir.startswith(media_root):
        try:
            if os.path.isdir(current_dir) and not os.listdir(current_dir):
                os.rmdir(current_dir)
            else:
                break
        except OSError:
            break

        current_dir = os.path.dirname(current_dir)


@receiver(post_delete, sender=User)
def delete_user_media_on_delete(sender, instance, **kwargs):
    _delete_file_and_dirs(instance.profile_image)
    _delete_file_and_dirs(instance.background_image)
