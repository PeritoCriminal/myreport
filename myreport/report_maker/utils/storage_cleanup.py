# report_maker/utils/storage_cleanup.py
from __future__ import annotations

import os
import shutil
from typing import Optional

from django.core.files.storage import FileSystemStorage


def delete_storage_prefix(storage, prefix: str) -> None:
    """
    Remove recursivamente tudo abaixo de um prefixo no storage.

    Comportamento:
    - Se o storage for FileSystemStorage, remove o diretório físico de uma vez
      (mais eficiente e garante remoção de subpastas).
    - Para outros storages, tenta varrer via listdir(prefix) e deletar arquivos
      e subdiretórios recursivamente.

    Parâmetros:
    - storage: instância de storage (ex.: default_storage ou field.storage).
    - prefix: caminho relativo no storage (ex.: 'reports/123/objects/app/model/uuid').

    Observações:
    - Prefixo vazio é ignorado.
    - A função é tolerante a erros (não deve quebrar o fluxo de deleção do sistema).
    """
    prefix = (prefix or "").strip().strip("/")
    if not prefix:
        return

    # Caso padrão (MEDIA_ROOT local): remover diretório físico
    if isinstance(storage, FileSystemStorage):
        try:
            abs_dir = storage.path(prefix)
        except Exception:
            return

        if os.path.isdir(abs_dir):
            shutil.rmtree(abs_dir, ignore_errors=True)
        return

    # Fallback genérico para outros storages
    _delete_storage_prefix_generic(storage, prefix)


def _delete_storage_prefix_generic(storage, prefix: str) -> None:
    """
    Implementação genérica (storages com listdir).
    """
    try:
        dirs, files = storage.listdir(prefix)
    except Exception:
        return

    for filename in files:
        try:
            storage.delete(f"{prefix}/{filename}")
        except Exception:
            pass

    for dirname in dirs:
        _delete_storage_prefix_generic(storage, f"{prefix}/{dirname}")

    # Alguns storages aceitam remover o "diretório" virtual; outros ignoram.
    try:
        storage.delete(prefix)
    except Exception:
        pass
