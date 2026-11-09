#!/usr/bin/env python3
"""D: carga la salida del job (part-00000) en la tabla `resultados` de PostgreSQL.
Uso (dentro del contenedor api):  python scripts/cargar_resultados.py [ruta/part-00000]
Es idempotente: vacia la tabla y vuelve a insertar (se puede re-ejecutar sin duplicar)."""
import os
import sys

import psycopg2
from psycopg2.extras import execute_values

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/data/output/resultado/part-00000"

DDL = """
CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    metodo_pago TEXT NOT NULL,
    dia_num SMALLINT NOT NULL CHECK (dia_num BETWEEN 1 AND 7),
    dia_semana TEXT NOT NULL,
    unidades_vendidas BIGINT NOT NULL CHECK (unidades_vendidas >= 0),
    UNIQUE (metodo_pago, dia_num)
)"""


def leer(ruta):
    filas = []
    with open(ruta, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            linea = linea.rstrip("\n")
            if not linea:
                continue
            try:
                llave, total = linea.split("\t")
                pago, dia, nombre = llave.split("|")
                filas.append((pago, int(dia), nombre, int(total)))
            except ValueError:
                print(f"linea {n} ignorada (formato invalido): {linea!r}", file=sys.stderr)
    return filas


def main():
    filas = leer(RUTA)
    if not filas:
        sys.exit(f"sin registros en {RUTA}")
    con = psycopg2.connect(host=os.environ.get("DB_HOST", "db"), port=os.environ.get("DB_PORT", "5432"),
                           dbname=os.environ["POSTGRES_DB"], user=os.environ["POSTGRES_USER"],
                           password=os.environ["POSTGRES_PASSWORD"])
    with con, con.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(42)")   # mismo lock que la API
        cur.execute(DDL)
        cur.execute("TRUNCATE resultados RESTART IDENTITY")
        execute_values(cur, "INSERT INTO resultados (metodo_pago, dia_num, dia_semana, unidades_vendidas) VALUES %s", filas)
    con.close()
    print(f"{len(filas)} registros cargados desde {RUTA}")


if __name__ == "__main__":
    main()
