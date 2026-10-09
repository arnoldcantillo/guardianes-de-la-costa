"""Capa JSON que usa la página web (index.html) para llamar a los escenarios."""
from __future__ import annotations

import base64
import json

from .bloques import aviso, lista, pares, tabla
from .escenarios import HISTORIAS, SALIDAS, Contexto, ejecutar_bloques, tabla_ruta, tabla_tramos
from .hu08_validacion import validar_entrada
from .nucleo import Grafo, Punto, tramos_ruta

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
    except (ValueError, KeyError, TypeError):
        bloques = [aviso("rojo", "Revisa los datos", "La latitud y la longitud deben ser números, por ejemplo 10.96 y -74.80.")]
        return json.dumps({"ok": False, "bloques": bloques}, ensure_ascii=False)
    r = validar_entrada(ctx.base, ctx.puntos)
    if not r.puede_calcular:
        bloques = [aviso("rojo", "El cálculo no se ejecutó", "Corrige estos datos y vuelve a aplicar:"), lista(r.errores)]
        return json.dumps({"ok": False, "bloques": bloques}, ensure_ascii=False)
    ruta = ctx.ruta()
    bloques = [aviso("verde", "Escenario aplicado", "Las pruebas de las historias usarán estos datos."),
               tabla_ruta(ruta),
               tabla_tramos(ruta),
               pares(("Base", ctx.base.nombre), ("Distancia total", f"{ruta.distancia_km:.2f} km"))]
    camino = [ruta.base]
    for t in tramos_ruta(ruta.base, ruta.puntos):
        camino.extend(t["nodos"][1:])
    grafo = Grafo([ruta.base, *ruta.puntos])
    aristas = [[{"lat": grafo.nodos[i].lat, "lon": grafo.nodos[i].lon},
                {"lat": grafo.nodos[j].lat, "lon": grafo.nodos[j].lon}]
               for i in range(len(grafo.nodos)) for j in grafo.ady[i] if i < j]
    mapa = {"base": {"nombre": ctx.base.nombre, "lat": ctx.base.lat, "lon": ctx.base.lon},
            "ruta": [{"nombre": p.nombre, "lat": p.lat, "lon": p.lon} for p in ruta.puntos],
            "camino": [{"lat": p.lat, "lon": p.lon} for p in camino],
            "aristas": aristas}
    return json.dumps({"ok": True, "bloques": bloques, "mapa": mapa}, ensure_ascii=False)


def ejecutar(hu: int, criterio: int, escenario_json: str) -> str:
    ctx = _contexto(json.loads(escenario_json))
    if SALIDAS.exists():
        for f in SALIDAS.iterdir():
            if f.is_file():
                f.unlink()
    ok, bloques = ejecutar_bloques(HISTORIAS[hu]["criterios"][criterio][1], ctx)
    archivos = []
    if SALIDAS.exists():
        for f in sorted(SALIDAS.iterdir()):
            if f.is_file():
                archivos.append({"nombre": f.name, "mime": MIME.get(f.suffix, "application/octet-stream"),
                                 "base64": base64.b64encode(f.read_bytes()).decode("ascii")})
    return json.dumps({"ok": ok, "bloques": bloques, "archivos": archivos}, ensure_ascii=False)
