# path: myreport/report_maker/signals/reportcase.py

from __future__ import annotations

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from report_maker.models import ReportCase
from report_maker.utils.storage_cleanup import delete_storage_prefix


@receiver(post_delete, sender=ReportCase)
def delete_reportcase_folder(sender, instance: ReportCase, **kwargs) -> None:
    """
    Remove integralmente a pasta do laudo e todas as suas
    subpastas no sistema de arquivos após a exclusão do
    registro correspondente no banco de dados.

    O diretório removido segue o padrão:

        reports/<report_case_id>/

    A remoção é executada após a confirmação da transação,
    assegurando consistência entre banco de dados e sistema
    de armazenamento.
    """
    prefix = f"reports/{instance.pk}"

    def _delete() -> None:
        delete_storage_prefix(default_storage, prefix)

    transaction.on_commit(_delete)
