# report_maker/utils/google_maps.py
from __future__ import annotations

import io
import re
import urllib.parse
import qrcode


class GoogleMapsLocationMixin:
    MAPS_SEARCH_URL = "https://www.google.com/maps/search/?api=1&query="

    def parse_location_line(self, value: str) -> dict:
        raw = value.strip()

        # URL direta (sem seguir redirect)
        if raw.startswith("http"):
            latlng = self._extract_latlng_from_url(raw)
            if latlng:
                return self._build_from_latlng(*latlng)
            return self._build_from_query(raw)

        norm = self._normalize_text(raw)

        for parser in (
            self._parse_decimal,
            self._parse_decimal_hemisphere,
            self._parse_dms,
        ):
            latlng = parser(norm)
            if latlng:
                return self._build_from_latlng(*latlng)

        return self._build_from_query(raw)

    # ───────── builders ─────────

    def _build_from_latlng(self, lat: float, lng: float) -> dict:
        query = f"{lat},{lng}"
        url = self.MAPS_SEARCH_URL + urllib.parse.quote(query)
        return {
            "maps_url": url,
            "lat": lat,
            "lng": lng,
            "raw_query": query,
            "qrcode_png": self._make_qrcode(url),
        }

    def _build_from_query(self, query: str) -> dict:
        url = self.MAPS_SEARCH_URL + urllib.parse.quote(query)
        return {
            "maps_url": url,
            "lat": None,
            "lng": None,
            "raw_query": query,
            "qrcode_png": self._make_qrcode(url),
        }

    # ───────── helpers ─────────

    def _make_qrcode(self, url: str) -> bytes:
        qr = qrcode.make(url)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        return buf.getvalue()

    def _extract_latlng_from_url(self, url: str):
        m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m:
            return float(m.group(1)), float(m.group(2))

        m = re.search(r"[?&](q|query)=(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if m:
            return float(m.group(2)), float(m.group(3))

        return None

    def _normalize_text(self, text: str) -> str:
        text = text.replace(";", ",")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"(\d),(\d)", r"\1.\2", text)
        return text.strip()

    def _parse_decimal(self, text: str):
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*,?\s*(-?\d+(?:\.\d+)?)", text)
        return (float(m.group(1)), float(m.group(2))) if m else None

    def _parse_decimal_hemisphere(self, text: str):
        m = re.search(
            r"(\d+(?:\.\d+)?)\s*([NS])\s*,?\s*(\d+(?:\.\d+)?)\s*([EW])",
            text,
            re.I,
        )
        if not m:
            return None

        lat = float(m.group(1)) * (-1 if m.group(2).upper() == "S" else 1)
        lng = float(m.group(3)) * (-1 if m.group(4).upper() == "W" else 1)
        return lat, lng

    def _parse_dms(self, text: str):
        dms = re.findall(
            r"(\d+)[°\s]+(\d+)[′'\s]+(\d+(?:\.\d+)?)[″\"\s]*([NSEW])",
            text,
            re.I,
        )
        if len(dms) != 2:
            return None

        def conv(d, m, s, h):
            val = float(d) + float(m) / 60 + float(s) / 3600
            return -val if h.upper() in ("S", "W") else val

        return conv(*dms[0]), conv(*dms[1])
