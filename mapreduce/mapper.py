#!/usr/bin/env python3
"""Mapper (Hadoop Streaming) - Pregunta 5: unidades vendidas por metodo de pago y dia de la semana.

Entrada : lineas CSV  id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago
Salida  : "<metodo_pago>|<dia_num>|<dia_nombre>\t<cantidad>"   (dia_num: 1=Lunes ... 7=Domingo)

- Ignora el encabezado (linea cuyo primer campo es 'id').
- Una linea mal formada NO tumba el job: se descarta y se cuenta en un counter de Hadoop.
"""
import sys
from datetime import date

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def contar(nombre):
    # Protocolo de counters de Hadoop Streaming (visibles al final del job)
    sys.stderr.write(f"reporter:counter:Mapper,{nombre},1\n")


def main():
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        campos = linea.split(",")
        if campos[0] == "id":                      # encabezado
            contar("encabezado_ignorado")
            continue
        if len(campos) != 8:
            contar("lineas_malformadas")
            continue
        try:
            dia = date.fromisoformat(campos[1][:10]).weekday()   # 0=Lunes
            cantidad = int(campos[5])
        except ValueError:
            contar("lineas_malformadas")
            continue
        pago = campos[7].strip()
        if not pago or cantidad <= 0:
            contar("lineas_malformadas")
            continue
        print(f"{pago}|{dia + 1}|{DIAS[dia]}\t{cantidad}")


if __name__ == "__main__":
    main()
