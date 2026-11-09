#!/usr/bin/env python3
"""C2: version secuencial (lectura linea a linea) de la MISMA pregunta.
Uso: python3 secuencial.py <csv> [salida]   -> mismo formato que part-00000 del job."""
import sys
from collections import defaultdict
from datetime import date

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def main(ruta, salida):
    acum = defaultdict(int)
    malas = 0
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            c = linea.split(",")
            if c[0] == "id":
                continue
            if len(c) != 8:
                malas += 1
                continue
            try:
                dia = date.fromisoformat(c[1][:10]).weekday()
                cantidad = int(c[5])
            except ValueError:
                malas += 1
                continue
            pago = c[7].strip()
            if not pago or cantidad <= 0:
                malas += 1
                continue
            acum[f"{pago}|{dia + 1}|{DIAS[dia]}"] += cantidad
    out = open(salida, "w", encoding="utf-8") if salida else sys.stdout
    for k in sorted(acum):
        out.write(f"{k}\t{acum[k]}\n")
    if salida:
        out.close()
    sys.stderr.write(f"lineas descartadas: {malas}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: secuencial.py <csv> [salida]")
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
