from __future__ import annotations

import math

from .hu10_tipo_residuo import validar_residuo
from .nucleo import COMPLETADO, OMITIDO, Ruta


class FormatoInvalido(ValueError):
    def __init__(self) -> None:
        super().__init__("Formato inválido")


def parsear_kg(valor: str | float | None) -> float:
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ValueError("El peso en kilogramos es obligatorio")
    try:
        kg = float(valor)
    except (TypeError, ValueError):
        raise FormatoInvalido() from None
    if kg < 0 or not math.isfinite(kg):
        raise FormatoInvalido()
    return kg


class RegistroJornada:
    def __init__(self, ruta: Ruta) -> None:
        self.ruta = ruta
        self.cerrada = False

    def completar_punto(self, nombre: str, kg: str | float | None, residuo: str | None) -> None:
        punto = next((p for p in self.ruta.puntos if p.nombre == nombre), None)
        if punto is None:
            raise ValueError(f"{nombre} no está en la ruta")
        peso = parsear_kg(kg)
        tipo = validar_residuo(residuo)
        punto.kg, punto.residuo, punto.estado = peso, tipo, COMPLETADO

    def cerrar_jornada(self) -> float:
        pendientes = [p.nombre for p in self.ruta.puntos if p.estado not in (COMPLETADO, OMITIDO)]
        if pendientes:
            raise ValueError("Faltan puntos por completar: " + ", ".join(pendientes))
        self.cerrada = True
        return sum(p.kg for p in self.ruta.puntos if p.estado == COMPLETADO)
