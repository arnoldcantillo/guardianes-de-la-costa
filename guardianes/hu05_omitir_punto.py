from __future__ import annotations

from dataclasses import replace

from .nucleo import OMITIDO, Ruta


class PuntoFijo(Exception):
    pass


def omitir_por_clima(ruta: Ruta, nombre: str) -> Ruta:
    if nombre == ruta.base.nombre or (ruta.puntos and nombre == ruta.puntos[-1].nombre):
        raise PuntoFijo("La base y el nodo final son puntos fijos obligatorios")
    if nombre not in [p.nombre for p in ruta.puntos]:
        raise ValueError(f"{nombre} no está en la ruta")
    nuevos = [replace(p, estado=OMITIDO) if p.nombre == nombre else replace(p)
              for p in ruta.puntos]
    return Ruta(ruta.id, ruta.base, nuevos)
