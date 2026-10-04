from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path

from .nucleo import Punto, Ruta

VACIO = "No hay rutas registradas hasta el momento"


@dataclass
class Registro:
    fecha: datetime
    ruta_id: str
    base: Punto
    puntos: list[Punto]
    distancia_km: float


class Historial:
    def __init__(self) -> None:
        self.registros: list[Registro] = []

    def guardar(self, ruta: Ruta, fecha: datetime | None = None) -> Registro:
        reg = Registro(fecha or datetime.now(), ruta.id, replace(ruta.base),
                       [replace(p) for p in ruta.puntos], ruta.distancia_km)
        self.registros.append(reg)
        return reg

    def listar(self, registros: list[Registro] | None = None) -> str:
        lista = self.registros if registros is None else registros
        if not self.registros or not lista:
            return VACIO if not self.registros else "Sin rutas en el período seleccionado"
        return "\n".join(
            f"{r.fecha:%Y-%m-%d %H:%M} | {r.ruta_id} | {r.distancia_km:.2f} km | "
            f"{len(r.puntos)} puntos: " + ", ".join(p.nombre for p in r.puntos)
            for r in sorted(lista, key=lambda r: r.fecha, reverse=True))

    def por_semana(self, referencia: date) -> list[Registro]:
        lunes = referencia - timedelta(days=referencia.weekday())
        return [r for r in self.registros if lunes <= r.fecha.date() < lunes + timedelta(days=7)]

    def por_mes(self, anio: int, mes: int) -> list[Registro]:
        return [r for r in self.registros if r.fecha.year == anio and r.fecha.month == mes]

    def guardar_json(self, archivo: str | Path) -> None:
        datos = [{**asdict(r), "fecha": r.fecha.isoformat()} for r in self.registros]
        Path(archivo).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def cargar_json(cls, archivo: str | Path) -> "Historial":
        h = cls()
        ruta = Path(archivo)
        if ruta.exists():
            for d in json.loads(ruta.read_text(encoding="utf-8")):
                h.registros.append(Registro(datetime.fromisoformat(d["fecha"]), d["ruta_id"],
                                            Punto(**d["base"]), [Punto(**p) for p in d["puntos"]],
                                            d["distancia_km"]))
        return h
