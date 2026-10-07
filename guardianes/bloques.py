"""Bloques de contenido estructurado para mostrar los resultados de los criterios.

Cada bloque es un diccionario con la clave "t" (tipo). La página web los dibuja como
tablas, avisos, listas y barras; a_texto() los convierte a texto plano para la consola
y para el simulador de escritorio.
"""
from __future__ import annotations

TONOS = ("rojo", "amarillo", "verde", "info")
TIPOS = ("p", "pares", "tabla", "lista", "aviso", "porcentajes", "barras", "documento")


def parrafo(texto: str) -> dict:
    return {"t": "p", "texto": texto}


def pares(*filas: tuple) -> dict:
    return {"t": "pares", "filas": [[str(k), str(v)] for k, v in filas]}


def celda(texto: str, tono: str) -> dict:
    return {"texto": str(texto), "tono": tono}


def tabla(cabeceras: list[str], filas: list[list]) -> dict:
    return {"t": "tabla", "cabeceras": list(cabeceras),
            "filas": [[c if isinstance(c, dict) else str(c) for c in fila] for fila in filas]}


def lista(items: list, ordenada: bool = False) -> dict:
    return {"t": "lista", "items": [str(i) for i in items], "ordenada": ordenada}


def aviso(tono: str, titulo: str, detalle: str | None = None) -> dict:
    return {"t": "aviso", "tono": tono, "titulo": titulo, "detalle": detalle}


def porcentajes(items: list[tuple]) -> dict:
    return {"t": "porcentajes", "items": [[str(e), float(p)] for e, p in items]}


def barras(titulo: str, unidad: str, valores: list[tuple]) -> dict:
    return {"t": "barras", "titulo": titulo, "unidad": unidad,
            "barras": [{"etiqueta": str(e), "valor": v} for e, v in valores]}


def documento(titulo: str, lineas: list[str]) -> dict:
    return {"t": "documento", "titulo": titulo, "lineas": list(lineas)}


def _txt(celda_) -> str:
    return celda_["texto"] if isinstance(celda_, dict) else str(celda_)


def a_texto(bloques: list[dict]) -> str:
    partes = []
    for b in bloques:
        t = b["t"]
        if t == "p":
            partes.append(b["texto"])
        elif t == "pares":
            partes.append("\n".join(f"{k}: {v}" for k, v in b["filas"]))
        elif t == "tabla":
            filas = [" | ".join(b["cabeceras"])] + [" | ".join(_txt(c) for c in f) for f in b["filas"]]
            partes.append("\n".join(filas))
        elif t == "lista":
            partes.append("\n".join(f"{i}. {x}" if b["ordenada"] else f"- {x}"
                                    for i, x in enumerate(b["items"], 1)))
        elif t == "aviso":
            partes.append(b["titulo"] + (f"\n{b['detalle']}" if b["detalle"] else ""))
        elif t == "porcentajes":
            partes.append("\n".join(f"- {e}: {p:g}%" for e, p in b["items"]))
        elif t == "barras":
            partes.append("\n".join([b["titulo"]] + [f"- {x['etiqueta']}: {x['valor']} {b['unidad']}" for x in b["barras"]]))
        elif t == "documento":
            partes.append("\n".join([b["titulo"], *b["lineas"]]))
    return "\n\n".join(partes)
