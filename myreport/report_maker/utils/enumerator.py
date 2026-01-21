# report_maker/utils/enumerator.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TitleEnumerator:
    """
    Enumeração hierárquica para títulos (até 3 níveis) e legendas de figura.

    Regras:
    - level=1 -> "1", "2", ...
      (zera t2 e t3)
    - level=2 -> "1.1", "1.2", ...
      (zera t3)
    - level=3 -> "1.1.1", "1.1.2", ...
    - level=0 -> "Figura 1", "Figura 2", ...
    - level=None/qualquer outro -> reset geral e retorna None

    Observação:
    - Estado é por instância (sem globais), seguro para uso em view/service, PDF e DOCX.
    """

    counters: Dict[str, int] = field(
        default_factory=lambda: {"t1": 0, "t2": 0, "t3": 0, "caption": 0}
    )

    def reset(self) -> None:
        self.counters["t1"] = 0
        self.counters["t2"] = 0
        self.counters["t3"] = 0
        self.counters["caption"] = 0

    def enumerate(self, level_title: Optional[int] = None) -> Optional[str]:
        if level_title == 1:
            self.counters["t1"] += 1
            self.counters["t2"] = 0
            self.counters["t3"] = 0
            return str(self.counters["t1"])

        if level_title == 2:
            # opcional: se ainda não houve título 1, inicia automaticamente
            if self.counters["t1"] == 0:
                self.counters["t1"] = 1
            self.counters["t2"] += 1
            self.counters["t3"] = 0
            return f"{self.counters['t1']}.{self.counters['t2']}"

        if level_title == 3:
            # opcional: se ainda não houve título 1/2, inicia automaticamente
            if self.counters["t1"] == 0:
                self.counters["t1"] = 1
            if self.counters["t2"] == 0:
                self.counters["t2"] = 1
            self.counters["t3"] += 1
            return f"{self.counters['t1']}.{self.counters['t2']}.{self.counters['t3']}"

        if level_title == 0:
            self.counters["caption"] += 1
            return f"Figura {self.counters['caption']}"

        self.reset()
        return None

    # Atalhos (opcional, mas deixa o código mais legível)
    def title(self, level: int) -> str:
        result = self.enumerate(level)
        if result is None:
            raise ValueError("Nível inválido para título.")
        return result

    def figure(self) -> str:
        result = self.enumerate(0)
        if result is None:
            raise RuntimeError("Falha inesperada ao enumerar figura.")
        return result
