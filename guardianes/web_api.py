"""Capa JSON que usa la página web (index.html) para llamar a los escenarios."""
from __future__ import annotations

import base64
import json

from .escenarios import HISTORIAS, SALIDAS, Contexto, ejecutar_criterio
from .hu08_validacion import validar_entrada
from .nucleo import Punto

MIME = {".pdf": "application/pdf", ".txt": "text/plain"}


def catalogo() -> str:
    return json.dumps([
        {"id": h["id"], "titulo": h["titulo"], "historia": h["historia"],
         "criterios": [d for d, _ in h["criterios"]]}
        for h in HISTORIAS], ensure_ascii=False)


def _contexto(escenario: dict) -> Contexto:
    b = escenario["base"]
    base = Punto(str(b["nombre"]).strip(), float(b["lat"]), float(b["lon"]))
    puntos = [Punto(str(p["nombre"]).strip(), float(p["lat"]), float(p["lon"])) for p in escenario["puntos"]]
    return Contexto(base, puntos)


def aplicar_escenario(escenario_json: str) -> str:
    try:
        ctx = _contexto(json.loads(escenario_json))
    except (ValueError, KeyError, TypeError) as e:
        return json.dumps({"ok": False, "texto": f"Datos no válidos: {e}"}, ensure_ascii=False)
    r = validar_entrada(ctx.base, ctx.puntos)
    if not r.puede_calcular:
        texto = "Validación (HU-08): el cálculo no se ejecutó\n- " + "\n- ".join(r.errores)
        return json.dumps({"ok": False, "texto": texto}, ensure_ascii=False)
    ruta = ctx.ruta()
    texto = "Escenario aplicado. Ruta óptima:\n" + "\n".join(ruta.detalle()) + f"\nDistancia total: {ruta.distancia_km:.2f} km"
    mapa = {"base": {"nombre": ctx.base.nombre, "lat": ctx.base.lat, "lon": ctx.base.lon},
            "ruta": [{"nombre": p.nombre, "lat": p.lat, "lon": p.lon} for p in ruta.puntos]}
    return json.dumps({"ok": True, "texto": texto, "mapa": mapa}, ensure_ascii=False)


def ejecutar(hu: int, criterio: int, escenario_json: str) -> str:
    ctx = _contexto(json.loads(escenario_json))
    if SALIDAS.exists():
        for f in SALIDAS.iterdir():
            if f.is_file():
                f.unlink()
    ok, texto = ejecutar_criterio(HISTORIAS[hu]["criterios"][criterio][1], ctx)
    archivos = []
    if SALIDAS.exists():
        for f in sorted(SALIDAS.iterdir()):
            if f.is_file():
                archivos.append({"nombre": f.name, "mime": MIME.get(f.suffix, "application/octet-stream"),
                                 "base64": base64.b64encode(f.read_bytes()).decode("ascii")})
    return json.dumps({"ok": ok, "texto": texto, "archivos": archivos}, ensure_ascii=False)
