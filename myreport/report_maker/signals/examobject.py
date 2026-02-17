# path: myreport/report_maker/signals/examobject.py

from __future__ import annotations

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from report_maker.models import ExamObject
from report_maker.utils.storage_cleanup import delete_storage_prefix


@receiver(post_delete)
def delete_examobject_folder(sender, instance, **kwargs) -> None:
    """
    Remove a pasta correspondente ao objeto examinado após a exclusão.

    Observação (herança multi-table):
      - Ao deletar um objeto concreto que herda de ExamObject, o Django dispara
        post_delete tanto para o modelo concreto quanto para ExamObject.
      - O caminho das imagens usa o ContentType do modelo concreto, portanto
        este handler atua somente quando o sender for o modelo concreto
        (subclasse de ExamObject), evitando calcular '.../examobject/...'.

    Padrão removido:

        reports/<report_case_id>/objects/<app_label>/<model_name>/<object_id>/
    """
    # Só interessa para subclasses concretas de ExamObject
    if not isinstance(instance, ExamObject):
        return

    # Ignora o disparo do modelo base, para não apagar caminho errado
    if sender is ExamObject:
        return

    prefix = (
        f"reports/{instance.report_case_id}/"
        f"objects/{sender._meta.app_label}/{sender._meta.model_name}/"
        f"{instance.pk}"
    )

    def _delete() -> None:
        delete_storage_prefix(default_storage, prefix)

    transaction.on_commit(_delete)
