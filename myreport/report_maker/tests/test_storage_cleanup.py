# report_maker/tests/test_storage_cleanup.py
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings

from accounts.models import User
from report_maker.models import GenericLocationExamObject, ObjectImage, ReportCase


# PNG válido 1x1 (bytes mínimos)
PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
    b"\xe2!\xbc3"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def make_user(*, i: int = 1) -> User:
    """Cria um usuário mínimo para satisfazer FKs obrigatórias (ReportCase.author)."""
    return User.objects.create_user(
        username=f"u{i}",
        email=f"u{i}@example.com",
        password="x",
    )


def make_reportcase(*, author: User, i: int = 1) -> ReportCase:
    """
    Cria um ReportCase com os campos obrigatórios preenchidos.
    Observação: o model faz full_clean() no save, então esses campos precisam existir.
    """
    return ReportCase.objects.create(
        report_number=f"{i:04d}/2026",
        author=author,
        requesting_authority="Autoridade requisitante (teste)",
        # outros campos podem ser opcionais no seu model; mantenha mínimo aqui
    )


def make_location_object(*, report: ReportCase, i: int = 1) -> GenericLocationExamObject:
    """Cria um objeto concreto simples que herda de ExamObject."""
    return GenericLocationExamObject.objects.create(
        report_case=report,
        title=f"Local {i} (teste)",
    )


class StorageCleanupSignalsTests(TransactionTestCase):
    """
    Testa remoção automática de arquivos/pastas no MEDIA_ROOT via signals:
    - delete de ObjectImage remove arquivo físico
    - delete de ExamObject (subclasse concreta) remove pasta do objeto
    - delete de ReportCase remove pasta do laudo

    Usamos TransactionTestCase para não mascarar callbacks de transaction.on_commit,
    caso o cleanup use on_commit internamente.
    """

    def setUp(self) -> None:
        super().setUp()
        self._tmpdir = tempfile.mkdtemp(prefix="myreport_media_")
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))

    def _media_path(self, rel: str) -> Path:
        return Path(self._tmpdir) / rel

    def _make_upload(self, name: str = "x.png") -> SimpleUploadedFile:
        return SimpleUploadedFile(
            name,
            PNG_1X1,
            content_type="image/png",
        )

    def test_delete_objectimage_removes_file(self):
        """Ao deletar ObjectImage, o arquivo físico deve ser removido do storage."""
        with override_settings(MEDIA_ROOT=self._tmpdir):
            author = make_user(i=1)
            report = make_reportcase(author=author, i=1)
            obj = make_location_object(report=report, i=1)

            img = ObjectImage.objects.create(
                content_object=obj,
                image=self._make_upload(),
                caption="teste",
                index=1,
                original_width=1,
                original_height=1,
            )

            file_abs = self._media_path(img.image.name)
            self.assertTrue(file_abs.exists(), f"Arquivo deveria existir: {file_abs}")

            img.delete()

            self.assertFalse(file_abs.exists(), f"Arquivo deveria ter sido deletado: {file_abs}")

    def test_delete_examobject_removes_object_folder(self):
        """
        Ao deletar um objeto concreto (subclasse de ExamObject),
        a pasta reports/<case>/objects/<app>/<model>/<id>/ deve ser removida.
        """
        with override_settings(MEDIA_ROOT=self._tmpdir):
            author = make_user(i=2)
            report = make_reportcase(author=author, i=2)
            obj = make_location_object(report=report, i=2)

            ObjectImage.objects.create(
                content_object=obj,
                image=self._make_upload(),
                index=1,
                original_width=1,
                original_height=1,
            )

            obj_dir = self._media_path(
                f"reports/{report.pk}/objects/"
                f"{obj._meta.app_label}/{obj._meta.model_name}/{obj.pk}"
            )
            self.assertTrue(obj_dir.exists(), f"Pasta do objeto deveria existir: {obj_dir}")

            obj.delete()

            self.assertFalse(obj_dir.exists(), f"Pasta do objeto deveria ter sido removida: {obj_dir}")

    def test_delete_reportcase_removes_report_folder(self):
        """Ao deletar ReportCase, a pasta reports/<case>/ deve ser removida por completo."""
        with override_settings(MEDIA_ROOT=self._tmpdir):
            author = make_user(i=3)
            report = make_reportcase(author=author, i=3)
            obj = make_location_object(report=report, i=3)

            ObjectImage.objects.create(
                content_object=obj,
                image=self._make_upload(),
                index=1,
                original_width=1,
                original_height=1,
            )

            report_dir = self._media_path(f"reports/{report.pk}")
            self.assertTrue(report_dir.exists(), f"Pasta do laudo deveria existir: {report_dir}")

            report.delete()

            self.assertFalse(report_dir.exists(), f"Pasta do laudo deveria ter sido removida: {report_dir}")
