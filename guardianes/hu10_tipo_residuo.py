from __future__ import annotations

from .nucleo import COMPLETADO, TIPOS_RESIDUO, Punto


def validar_residuo(valor: str | None) -> str:
    if valor not in TIPOS_RESIDUO:
        raise ValueError("Seleccione el tipo de residuo: " + ", ".join(TIPOS_RESIDUO))
    return valor


def filtrar_historial(registros: list, tipo: str) -> list[tuple]:
    validar_residuo(tipo)
    salida = []
    for registro in registros:
        nodos = [p for p in registro.puntos if p.residuo == tipo]
        if nodos:
            salida.append((registro, nodos))
    return salida


def desglose_porcentual(puntos: list[Punto]) -> dict[str, float]:
    completados = [p for p in puntos if p.estado == COMPLETADO and p.residuo]
    total = sum(p.kg for p in completados)
    return {
        tipo: (round(100 * sum(p.kg for p in completados if p.residuo == tipo) / total, 1)
               if total > 0 else 0.0)
        for tipo in TIPOS_RESIDUO
    }
