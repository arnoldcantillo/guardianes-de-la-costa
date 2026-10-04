from __future__ import annotations

import re
from dataclasses import dataclass, field

from .nucleo import Punto, dentro_de_limites

_COORD = re.compile(r"^-?\d{1,3}(\.\d+)?$")


class ErrorValidacion(ValueError):
    pass


@dataclass
class Resultado:
    errores: list[str] = field(default_factory=list)

    @property
    def puede_calcular(self) -> bool:
        return not self.errores


def validar_coordenada_texto(texto: str, campo: str = "coordenada") -> float:
    limpio = texto.strip()
    if not _COORD.match(limpio):
        raise ErrorValidacion(f"Error de sintaxis en {campo}: solo se permiten números, punto y signo -")
    return float(limpio)


def validar_entrada(base: Punto | None, puntos: list[Punto]) -> Resultado:
    r = Resultado()
    if base is None:
        r.errores.append("Dato vacío: falta la base")
        candidatos = list(puntos)
    else:
        candidatos = [base, *puntos]
    if not puntos:
        r.errores.append("Dato vacío: no hay puntos de recolección")
    nombres: set[str] = set()
    coords: set[tuple[float, float]] = set()
    for p in candidatos:
        if not p.nombre.strip():
            r.errores.append("Dato vacío: hay un punto sin nombre")
        if not dentro_de_limites(p.lat, p.lon):
            r.errores.append(f"Fuera de rango: {p.nombre} ({p.lat}, {p.lon})")
        if p.nombre in nombres:
            r.errores.append(f"Duplicado: el nombre {p.nombre}")
        if (p.lat, p.lon) in coords:
            r.errores.append(f"Duplicado: las coordenadas de {p.nombre}")
        nombres.add(p.nombre)
        coords.add((p.lat, p.lon))
    return r


def exigir_validos(base: Punto | None, puntos: list[Punto]) -> None:
    r = validar_entrada(base, puntos)
    if not r.puede_calcular:
        raise ErrorValidacion("; ".join(r.errores))
