"""Simulador visual de las 14 historias de usuario. Ejecutar con: py simulador.py"""
import tkinter as tk
from tkinter import scrolledtext, ttk

from guardianes.escenarios import HISTORIAS, Contexto, ejecutar_criterio, ejecutar_todos
from guardianes.hu02_coordenadas import calcular_ruta
from guardianes.hu08_validacion import validar_entrada
from guardianes.nucleo import Punto

VERDE, ROJO = "#0a7d2c", "#b00020"
FUENTE_TEXTO = ("Consolas", 11)

PUNTOS_DEFECTO = """Dársena 1, 10.99, -74.85
Desembocadura, 10.93, -74.78
Canal Norte, 11.02, -74.79
Muelle viejo, 10.95, -74.88"""


def nueva_salida(padre) -> scrolledtext.ScrolledText:
    t = scrolledtext.ScrolledText(padre, height=14, font=FUENTE_TEXTO, wrap="word")
    t.tag_config("ok", foreground=VERDE, font=("Consolas", 11, "bold"))
    t.tag_config("mal", foreground=ROJO, font=("Consolas", 11, "bold"))
    t.tag_config("tit", font=("Segoe UI", 10, "bold"))
    return t


def escribir(salida, ok: bool, titulo: str, cuerpo: str) -> None:
    salida.insert("end", ("✔ CUMPLE  " if ok else "✘ NO CUMPLE  "), "ok" if ok else "mal")
    salida.insert("end", titulo + "\n", "tit")
    salida.insert("end", cuerpo + "\n\n")
    salida.see("end")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Simulador - Optimizador de enrutamiento costero · Guardianes de la costera")
        self.geometry("1200x780")
        self.ctx = Contexto.por_defecto()
        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True)
        self._pestana_escenario()
        for h in HISTORIAS:
            self._pestana_historia(h)
        self._pestana_resumen()

    # ----------------------------------------------------------- escenario
    def _pestana_escenario(self) -> None:
        f = ttk.Frame(self.cuaderno, padding=10)
        self.cuaderno.add(f, text="Escenario")
        ttk.Label(f, text="Datos de la jornada", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(f, text="Todas las pruebas de las historias usan estos datos. Puedes cambiarlos y volver a aplicarlos.",
                  wraplength=1100).pack(anchor="w", pady=(2, 8))

        fila = ttk.Frame(f)
        fila.pack(anchor="w")
        self.base_nombre, self.base_lat, self.base_lon = (tk.StringVar(value=v) for v in ("Muelle Centro", "10.96", "-74.80"))
        for etiqueta, var, ancho in (("Base:", self.base_nombre, 18), ("Latitud:", self.base_lat, 10), ("Longitud:", self.base_lon, 10)):
            ttk.Label(fila, text=etiqueta).pack(side="left", padx=(0, 4))
            ttk.Entry(fila, textvariable=var, width=ancho).pack(side="left", padx=(0, 14))

        ttk.Label(f, text="Puntos de acumulación (uno por línea: nombre, latitud, longitud), en el orden de ingreso:").pack(anchor="w", pady=(10, 2))
        self.puntos_texto = tk.Text(f, height=7, width=60, font=FUENTE_TEXTO)
        self.puntos_texto.insert("1.0", PUNTOS_DEFECTO)
        self.puntos_texto.pack(anchor="w")

        ttk.Button(f, text="Aplicar y calcular ruta óptima", command=self._aplicar_escenario).pack(anchor="w", pady=8)
        self.salida_escenario = nueva_salida(f)
        self.salida_escenario.pack(fill="both", expand=True)

    def _aplicar_escenario(self) -> None:
        s = self.salida_escenario
        s.delete("1.0", "end")
        try:
            base = Punto(self.base_nombre.get().strip(), float(self.base_lat.get()), float(self.base_lon.get()))
            puntos = []
            for n, linea in enumerate(self.puntos_texto.get("1.0", "end").splitlines(), 1):
                if not linea.strip():
                    continue
                partes = [x.strip() for x in linea.split(",")]
                if len(partes) != 3:
                    raise ValueError(f"Línea {n}: use «nombre, latitud, longitud»")
                puntos.append(Punto(partes[0], float(partes[1]), float(partes[2])))
        except ValueError as e:
            escribir(s, False, "Datos no válidos", str(e))
            return
        r = validar_entrada(base, puntos)
        if not r.puede_calcular:
            escribir(s, False, "Validación (HU-08): el cálculo no se ejecutó", "- " + "\n- ".join(r.errores))
            return
        self.ctx = Contexto(base, puntos)
        ruta = calcular_ruta(base, [Punto(p.nombre, p.lat, p.lon) for p in puntos])
        escribir(s, True, "Escenario aplicado. Ruta óptima:", "\n".join(ruta.detalle()) + f"\nDistancia total: {ruta.distancia_km:.2f} km")

    # ------------------------------------------------------------ historias
    def _pestana_historia(self, h: dict) -> None:
        f = ttk.Frame(self.cuaderno, padding=10)
        self.cuaderno.add(f, text=h["id"])
        ttk.Label(f, text=f'{h["id"]} · {h["titulo"]}', font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(f, text=h["historia"], wraplength=1130, justify="left").pack(anchor="w", pady=(4, 10))
        salida = nueva_salida(f)

        for n, (desc, fn) in enumerate(h["criterios"], 1):
            fila = ttk.Frame(f)
            fila.pack(fill="x", pady=2)
            ttk.Button(fila, text=f"Probar criterio {n}", width=18,
                       command=lambda n=n, d=desc, fn=fn, s=salida: self._probar(s, n, d, fn)).pack(side="left")
            ttk.Label(fila, text=desc, wraplength=950, justify="left").pack(side="left", padx=10)

        botones = ttk.Frame(f)
        botones.pack(fill="x", pady=8)
        ttk.Button(botones, text="Probar los 3 criterios",
                   command=lambda: [self._probar(salida, n, d, fn) for n, (d, fn) in enumerate(h["criterios"], 1)]).pack(side="left")
        ttk.Button(botones, text="Limpiar", command=lambda: salida.delete("1.0", "end")).pack(side="left", padx=8)
        salida.pack(fill="both", expand=True)

    def _probar(self, salida, n: int, desc: str, fn) -> None:
        ok, texto = ejecutar_criterio(fn, self.ctx)
        escribir(salida, ok, f"Criterio {n}: {desc}", texto)

    # -------------------------------------------------------------- resumen
    def _pestana_resumen(self) -> None:
        f = ttk.Frame(self.cuaderno, padding=10)
        self.cuaderno.add(f, text="Resumen")
        ttk.Label(f, text="Resumen de las 14 historias", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        self.etiqueta_total = ttk.Label(f, text="Aún no se ha ejecutado.", font=("Segoe UI", 12))
        self.etiqueta_total.pack(anchor="w", pady=6)
        ttk.Button(f, text="Ejecutar los 42 criterios", command=self._ejecutar_todos).pack(anchor="w")
        self.salida_resumen = nueva_salida(f)
        self.salida_resumen.pack(fill="both", expand=True, pady=8)

    def _ejecutar_todos(self) -> None:
        s = self.salida_resumen
        s.delete("1.0", "end")
        resultados = ejecutar_todos(self.ctx)
        for hu, n, desc, ok, _ in resultados:
            s.insert("end", ("✔ " if ok else "✘ "), "ok" if ok else "mal")
            s.insert("end", f"{hu} · criterio {n}: {desc}\n")
        cumplen = sum(1 for r in resultados if r[3])
        self.etiqueta_total.config(text=f"{cumplen} de {len(resultados)} criterios cumplidos",
                                   foreground=VERDE if cumplen == len(resultados) else ROJO)


if __name__ == "__main__":
    App().mainloop()
