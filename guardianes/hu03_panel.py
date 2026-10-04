from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class Jornada:
    fecha: date
    combustible_real_l: float
    combustible_sin_optimizador_l: float
    plastico_kg: float


class PanelControl:
    def __init__(self) -> None:
        self.jornadas: list[Jornada] = []

    def registrar(self, jornada: Jornada) -> None:
        self.jornadas.append(jornada)

    def resumen_mes(self, anio: int, mes: int) -> dict[str, float]:
        del_mes = [j for j in self.jornadas if j.fecha.year == anio and j.fecha.month == mes]
        real = sum(j.combustible_real_l for j in del_mes)
        sin_opt = sum(j.combustible_sin_optimizador_l for j in del_mes)
        return {
            "combustible_real_l": round(real, 2),
            "combustible_sin_optimizador_l": round(sin_opt, 2),
            "combustible_ahorrado_l": round(sin_opt - real, 2),
            "plastico_kg": round(sum(j.plastico_kg for j in del_mes), 2),
        }

    def grafico_barras(self, anio: int, mes: int, ancho: int = 40) -> str:
        r = self.resumen_mes(anio, mes)
        real, sin_opt = r["combustible_real_l"], r["combustible_sin_optimizador_l"]
        maximo = max(real, sin_opt, 1e-9)

        def barra(valor: float) -> str:
            return "#" * round(ancho * valor / maximo)

        return "\n".join([
            f"Combustible {mes:02d}/{anio}",
            f"Con optimizador {barra(real):<{ancho}} {real} L",
            f"Sin optimizador {barra(sin_opt):<{ancho}} {sin_opt} L",
            f"Plástico retirado: {r['plastico_kg']} kg",
        ])

    def generar_pdf(self, anio: int, mes: int, destino: str | Path) -> Path:
        r = self.resumen_mes(anio, mes)
        real, sin_opt = r["combustible_real_l"], r["combustible_sin_optimizador_l"]
        maximo = max(real, sin_opt, 1e-9)
        base_y, alto_max = 500, 200
        h_real, h_sin = alto_max * real / maximo, alto_max * sin_opt / maximo
        c: list[str] = []

        def texto(x: int, y: int, t: str, tam: int = 12) -> None:
            seguro = t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            c.append(f"BT /F1 {tam} Tf {x} {y} Td ({seguro}) Tj ET")

        texto(60, 780, "Panel de control - Guardianes de la costera", 16)
        texto(60, 755, f"Mes: {mes:02d}/{anio}")
        texto(60, 735, f"Plástico retirado: {r['plastico_kg']} kg")
        texto(60, 715, f"Combustible ahorrado: {r['combustible_ahorrado_l']} L")
        c.append(f"0.2 0.4 0.8 rg 120 {base_y} 100 {h_real:.2f} re f")
        c.append(f"0.6 0.6 0.6 rg 300 {base_y} 100 {h_sin:.2f} re f")
        c.append("0 g")
        texto(120, base_y - 20, "Con optimizador")
        texto(300, base_y - 20, "Sin optimizador")
        texto(120, int(base_y + h_real + 8), f"{real} L")
        texto(300, int(base_y + h_sin + 8), f"{sin_opt} L")

        flujo = "\n".join(c).encode("latin-1", "replace")
        objetos = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(flujo)).encode() + b" >>\nstream\n" + flujo + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        ]
        pdf, offsets = b"%PDF-1.4\n", []
        for i, obj in enumerate(objetos, 1):
            offsets.append(len(pdf))
            pdf += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
        xref = len(pdf)
        pdf += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
        for o in offsets:
            pdf += f"{o:010d} 00000 n \n".encode()
        pdf += (f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref}\n%%EOF\n").encode()
        destino = Path(destino)
        destino.write_bytes(pdf)
        return destino
