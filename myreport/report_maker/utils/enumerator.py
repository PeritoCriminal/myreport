# report_maker/utils/enumerator.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TitleEnumerator:
    """
    Enumeração hierárquica para títulos (até 3 níveis) e legendas de figura.

    Títulos:
      level=1 -> "1", "2", ...
      level=2 -> "1.1", "1.2", ...
      level=3 -> "1.1.1", ...

    Figuras:
      figure() -> "Figura 1", "Figura 2", ...

    Controles:
      - strict=True: não permite pular níveis (ex.: pedir level=2 sem ter level=1)
      - reset_titles(): zera t1/t2/t3
      - reset_figures(): zera contagem de figuras
      - reset_all(): zera tudo
    """

    strict: bool = True
    counters: Dict[str, int] = field(
        default_factory=lambda: {"t1": 0, "t2": 0, "t3": 0, "caption": 0}
    )

    # -----------------------
    # Resets
    # -----------------------
    def reset_titles(self) -> None:
        self.counters["t1"] = 0
        self.counters["t2"] = 0
        self.counters["t3"] = 0

    def reset_figures(self) -> None:
        self.counters["caption"] = 0

    def reset_all(self) -> None:
        self.reset_titles()
        self.reset_figures()

    # -----------------------
    # Enumeração principal
    # -----------------------
    def enumerate(self, level_title: Optional[int] = None) -> Optional[str]:
        if level_title == 1:
            self.counters["t1"] += 1
            self.counters["t2"] = 0
            self.counters["t3"] = 0
            return str(self.counters["t1"])

        if level_title == 2:
            if self.counters["t1"] == 0:
                if self.strict:
                    raise ValueError("Título nível 2 sem existir nível 1.")
                self.counters["t1"] = 1  # fallback não-estrito

            self.counters["t2"] += 1
            self.counters["t3"] = 0
            return f"{self.counters['t1']}.{self.counters['t2']}"

        if level_title == 3:
            if self.counters["t1"] == 0 or self.counters["t2"] == 0:
                if self.strict:
                    raise ValueError("Título nível 3 sem existir nível 1 e 2.")
                # fallback não-estrito
                if self.counters["t1"] == 0:
                    self.counters["t1"] = 1
                if self.counters["t2"] == 0:
                    self.counters["t2"] = 1

            self.counters["t3"] += 1
            return f"{self.counters['t1']}.{self.counters['t2']}.{self.counters['t3']}"

        if level_title == 0:
            self.counters["caption"] += 1
            return f"Figura {self.counters['caption']}"

        # nível inválido: não reseta “sem querer”
        return None

    # -----------------------
    # Atalhos
    # -----------------------
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
