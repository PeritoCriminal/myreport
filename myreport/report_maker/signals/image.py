# path: myreport/report_maker/signals/image.py

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from report_maker.models import ObjectImage


@receiver(post_delete, sender=ObjectImage)
def delete_objectimage_file(sender, instance: ObjectImage, **kwargs) -> None:
    """
    Remove o arquivo físico associado à instância de ObjectImage
    após a exclusão do registro no banco de dados.

    A deleção ocorre apenas após a confirmação da transação
    (transaction.on_commit), prevenindo inconsistências caso
    haja rollback.

    Abrange exclusões realizadas via:
    - View
    - Admin
    - Shell
    - Cascata (on_delete=CASCADE)
    """
    file_field = getattr(instance, "image", None)
    name = getattr(file_field, "name", "") or ""
    if not name:
        return

    storage = file_field.storage

    def _delete() -> None:
        try:
            if storage.exists(name):
                storage.delete(name)
        except Exception:
            pass

    transaction.on_commit(_delete)
