from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class EntradaAuditoria:
    momento: datetime
    usuario: str
    accion: str
    ruta_planificada: tuple[str, ...]
    ruta_ejecutada: tuple[str, ...]


class Auditoria:
    def __init__(self) -> None:
        self._entradas: list[EntradaAuditoria] = []

    def registrar(self, usuario: str, accion: str, ruta_planificada: list[str],
                  ruta_ejecutada: list[str]) -> None:
        self._entradas.append(EntradaAuditoria(
            datetime.now(), usuario, accion, tuple(ruta_planificada), tuple(ruta_ejecutada)))

    def buscar_por_fecha(self, dia: date) -> tuple[EntradaAuditoria, ...]:
        return tuple(e for e in self._entradas if e.momento.date() == dia)

    def tabla_comparativa(self, dia: date) -> str:
        filas = ["Fecha y hora | Usuario | Acción | Ruta planificada inicialmente | Ruta ejecutada"]
        for e in self.buscar_por_fecha(dia):
            filas.append(f"{e.momento:%Y-%m-%d %H:%M:%S} | {e.usuario} | {e.accion} | "
                         f"{' > '.join(e.ruta_planificada)} | {' > '.join(e.ruta_ejecutada)}")
        return "\n".join(filas)

    def eliminar(self, *_args, **_kwargs) -> None:
        raise PermissionError("Acceso denegado: los registros de auditoría son de solo lectura")

    def modificar(self, *_args, **_kwargs) -> None:
        raise PermissionError("Acceso denegado: los registros de auditoría son de solo lectura")
