from __future__ import annotations

import json
from pathlib import Path

from .nucleo import Embarcacion

ESTANDAR = "Lancha Estándar"

# Valores de ejemplo; ajustar a las lanchas reales.
BASE = [
    Embarcacion(ESTANDAR, "Genérica", 1.2, 80),
    Embarcacion("Lancha Rápida", "Fibra 25", 2.0, 120),
    Embarcacion("Lancha de Carga", "Barcaza 40", 3.0, 200),
]


class Catalogo:
    def __init__(self, archivo: str | Path | None = None) -> None:
        self.archivo = Path(archivo) if archivo else None
        self.items = {e.nombre: e for e in BASE}
        if self.archivo and self.archivo.exists():
            for d in json.loads(self.archivo.read_text(encoding="utf-8")):
                self.items[d["nombre"]] = Embarcacion(**d)

    def agregar(self, nombre: str, modelo: str, consumo_l_km: float, tanque_l: float = 100.0) -> Embarcacion:
        if not nombre.strip() or not modelo.strip():
            raise ValueError("Nombre y modelo son obligatorios")
        if consumo_l_km <= 0 or tanque_l <= 0:
            raise ValueError("El consumo y el tanque deben ser mayores que cero")
        nueva = Embarcacion(nombre.strip(), modelo.strip(), consumo_l_km, tanque_l)
        self.items[nueva.nombre] = nueva
        self._guardar()
        return nueva

    def _guardar(self) -> None:
        if self.archivo:
            extras = [vars(e) for e in self.items.values() if e not in BASE]
            self.archivo.write_text(json.dumps(extras, ensure_ascii=False, indent=2), encoding="utf-8")

    def seleccionar(self, nombre: str | None = None) -> tuple[Embarcacion, str | None]:
        if nombre is None:
            return self.items[ESTANDAR], f"No se seleccionó embarcación: se usa {ESTANDAR}."
        if nombre not in self.items:
            raise ValueError(f"La embarcación {nombre} no está en el catálogo")
        return self.items[nombre], None


def consumo_ruta(distancia_km: float, embarcacion: Embarcacion) -> float:
    return distancia_km * embarcacion.consumo_l_km
