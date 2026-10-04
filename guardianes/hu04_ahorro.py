from __future__ import annotations

from dataclasses import dataclass

from .nucleo import Embarcacion, Punto, longitud_ruta, optimizar_ruta

META_MIN, META_MAX = 15.0, 20.0


@dataclass
class Ahorro:
    km_empirico: float
    km_calculado: float
    litros_ahorrados: float

    @property
    def porcentaje(self) -> float:
        if self.km_empirico <= 0 or abs(self.km_empirico - self.km_calculado) < 1e-9:
            return 0.0
        return 100 * (self.km_empirico - self.km_calculado) / self.km_empirico

    @property
    def alcanza_meta(self) -> bool:
        return self.porcentaje >= META_MIN

    def reporte(self) -> str:
        if self.porcentaje == 0.0:
            lineas = ["Ahorro de distancia: 0%", "La ruta actual es óptima."]
        else:
            meta = "alcanza" if self.alcanza_meta else "no alcanza"
            lineas = [f"Ahorro de distancia: {self.porcentaje:.1f}%",
                      f"{meta.capitalize()} la meta de {META_MIN:.0f}% a {META_MAX:.0f}%."]
        lineas.append(f"Ahorro estimado de combustible: {self.litros_ahorrados:.2f} litros")
        return "\n".join(lineas)


def estimar_ahorro(base: Punto, puntos_en_orden_de_ingreso: list[Punto],
                   embarcacion: Embarcacion, ruta_calculada: list[Punto] | None = None) -> Ahorro:
    calculada = ruta_calculada or optimizar_ruta(base, puntos_en_orden_de_ingreso)
    km_emp = longitud_ruta(base, puntos_en_orden_de_ingreso)
    km_calc = longitud_ruta(base, calculada)
    return Ahorro(km_emp, km_calc, embarcacion.combustible_para(km_emp - km_calc))
