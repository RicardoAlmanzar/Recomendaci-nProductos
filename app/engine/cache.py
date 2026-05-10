"""
Capa de cache — Módulo 11.

Implementación en memoria con TTL manual. La interfaz pública es idéntica
a lo que se usaría con Redis, permitiendo un swap futuro sin cambiar
ningún archivo que consuma esta clase.
"""
from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Optional


class RecommendationCache:
    """
    Cache con TTL configurable vía CACHE_TTL_SECONDS (default 300s).

    Interfaz Redis-compatible:
        get(key)          → valor o None
        set(key, value)   → guarda con TTL
        invalidate(key)   → elimina entrada
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self.ttl: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))

    # ── Interfaz pública ───────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """Retorna el valor asociado a key, o None si no existe o expiró."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if time.monotonic() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Guarda value bajo key con el TTL configurado."""
        self._store[key] = (time.monotonic() + self.ttl, value)

    def invalidate(self, key: str) -> None:
        """Elimina la entrada si existe."""
        self._store.pop(key, None)

    # ── Generación de keys ─────────────────────────────────────────────

    def make_request_key(
        self,
        customer_id: str,
        session_id: Optional[str],
        page_type: str,
        slot: str,
    ) -> str:
        """Hash determinístico de los parámetros del request."""
        raw = f"{customer_id}:{session_id or ''}:{page_type}:{slot}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def make_id_key(self, recommendation_id: str) -> str:
        """Key para lookup por recommendation_id (debugging/auditoría)."""
        return f"rec_id:{recommendation_id}"


# Singleton — compartido por todos los requests
cache = RecommendationCache()
