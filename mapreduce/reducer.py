#!/usr/bin/env python3
"""Reducer (y combiner) - suma las unidades por llave.
Hadoop entrega las llaves ordenadas, por eso basta con acumular mientras la llave no cambie.
Como la suma es asociativa y conmutativa, el mismo script sirve como combiner."""
import sys

llave_actual, total = None, 0
for linea in sys.stdin:
    try:
        llave, valor = linea.rstrip("\n").split("\t")
        valor = int(valor)
    except ValueError:
        continue                                    # linea corrupta: se ignora
    if llave == llave_actual:
        total += valor
    else:
        if llave_actual is not None:
            print(f"{llave_actual}\t{total}")
        llave_actual, total = llave, valor
if llave_actual is not None:
    print(f"{llave_actual}\t{total}")
