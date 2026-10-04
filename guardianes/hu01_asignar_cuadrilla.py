from __future__ import annotations

from dataclasses import dataclass

from .nucleo import Ruta

DISPONIBLE = "Disponible"
EN_OPERACION = "En Operación"


class AsignacionRechazada(Exception):
    pass


@dataclass
class Cuadrilla:
    nombre: str
    estado: str = DISPONIBLE
    ruta_id: str | None = None


class Despacho:
    def __init__(self, cuadrillas: list[Cuadrilla]) -> None:
        self.cuadrillas = {c.nombre: c for c in cuadrillas}

    def disponibles(self) -> list[Cuadrilla]:
        return [c for c in self.cuadrillas.values() if c.estado == DISPONIBLE]

    def asignar(self, ruta: Ruta, nombre_cuadrilla: str) -> Cuadrilla:
        if nombre_cuadrilla not in self.cuadrillas:
            raise ValueError(f"La cuadrilla {nombre_cuadrilla} no existe")
        cuadrilla = self.cuadrillas[nombre_cuadrilla]
        if cuadrilla.estado == EN_OPERACION:
            raise AsignacionRechazada(
                f"Advertencia: {cuadrilla.nombre} ya está En Operación (ruta {cuadrilla.ruta_id})")
        cuadrilla.estado = EN_OPERACION
        cuadrilla.ruta_id = ruta.id
        return cuadrilla

    def finalizar(self, nombre_cuadrilla: str) -> None:
        cuadrilla = self.cuadrillas[nombre_cuadrilla]
        cuadrilla.estado = DISPONIBLE
        cuadrilla.ruta_id = None

    def panel_general(self) -> dict[str, str]:
        return {c.nombre: c.estado for c in self.cuadrillas.values()}
