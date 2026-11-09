"""API DataMart - CRUD sobre la tabla `resultados`
(unidades vendidas por metodo de pago y dia de la semana)."""
import os
import time

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}

DDL = """
CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    metodo_pago TEXT NOT NULL,
    dia_num SMALLINT NOT NULL CHECK (dia_num BETWEEN 1 AND 7),
    dia_semana TEXT NOT NULL,
    unidades_vendidas BIGINT NOT NULL CHECK (unidades_vendidas >= 0),
    UNIQUE (metodo_pago, dia_num)
)"""


def conectar(reintentos=15):
    for i in range(reintentos):
        try:
            return psycopg2.connect(
                host=os.environ.get("DB_HOST", "db"),
                port=os.environ.get("DB_PORT", "5432"),
                dbname=os.environ["POSTGRES_DB"],
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
            )
        except psycopg2.OperationalError:
            if i == reintentos - 1:
                raise
            time.sleep(2)


def consulta(sql, params=(), uno=False, commit=False):
    con = conectar()
    try:
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            filas = (cur.fetchone() if uno else cur.fetchall()) if cur.description else None
        if commit:
            con.commit()
        return filas
    finally:
        con.close()


def iniciar_tabla():
    con = conectar()
    with con, con.cursor() as cur:
        # Los 2 workers de gunicorn arrancan a la vez: el lock serializa el CREATE TABLE
        # (sin el, con la BD vacia ambos chocan con UniqueViolation en pg_class).
        cur.execute("SELECT pg_advisory_xact_lock(42)")
        cur.execute(DDL)
    con.close()


iniciar_tabla()


@app.get("/")
def raiz():
    return jsonify(servicio="DataMart API", pregunta="Unidades vendidas por método de pago y día de la semana",
                   endpoints=["GET /resultados", "GET /resultados/<metodo_pago>[?dia=1..7]",
                              "POST /resultados", "PUT /resultados/<id>", "DELETE /resultados/<id>"])


@app.get("/health")
def health():
    consulta("SELECT 1")
    return jsonify(status="ok")


@app.get("/resultados")
def listar():
    filas = consulta("SELECT * FROM resultados ORDER BY metodo_pago, dia_num")
    return jsonify(total_registros=len(filas), resultados=filas)


@app.get("/resultados/<clave>")
def por_clave(clave):
    """clave = metodo_pago (Efectivo, Tarjeta, Transferencia, Vales). Filtro opcional ?dia=1..7"""
    sql, params = "SELECT * FROM resultados WHERE lower(metodo_pago) = lower(%s)", [clave]
    if request.args.get("dia"):
        sql += " AND dia_num = %s"
        params.append(request.args["dia"])
    filas = consulta(sql + " ORDER BY dia_num", params)
    if not filas:
        return jsonify(error=f"sin resultados para '{clave}'"), 404
    return jsonify(metodo_pago=filas[0]["metodo_pago"],
                   total_unidades=sum(f["unidades_vendidas"] for f in filas), resultados=filas)


def _validar(d, parcial=False):
    campos = {}
    if "metodo_pago" in d:
        campos["metodo_pago"] = str(d["metodo_pago"]).strip()
    if "dia_num" in d:
        dia = int(d["dia_num"])
        if dia not in DIAS:
            raise ValueError("dia_num debe estar entre 1 y 7")
        campos["dia_num"], campos["dia_semana"] = dia, DIAS[dia]
    if "unidades_vendidas" in d:
        campos["unidades_vendidas"] = int(d["unidades_vendidas"])
        if campos["unidades_vendidas"] < 0:
            raise ValueError("unidades_vendidas no puede ser negativa")
    if not parcial and not {"metodo_pago", "dia_num", "unidades_vendidas"} <= d.keys():
        raise ValueError("se requieren metodo_pago, dia_num y unidades_vendidas")
    if not campos:
        raise ValueError("nada que actualizar")
    return campos


@app.post("/resultados")
def crear():
    try:
        c = _validar(request.get_json(force=True, silent=True) or {})
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400
    try:
        fila = consulta(
            "INSERT INTO resultados (metodo_pago, dia_num, dia_semana, unidades_vendidas) "
            "VALUES (%(metodo_pago)s, %(dia_num)s, %(dia_semana)s, %(unidades_vendidas)s) RETURNING *",
            c, uno=True, commit=True)
    except psycopg2.errors.UniqueViolation:
        return jsonify(error="ya existe ese metodo_pago/dia_num; usa PUT"), 409
    return jsonify(fila), 201


@app.put("/resultados/<int:rid>")
def actualizar(rid):
    try:
        c = _validar(request.get_json(force=True, silent=True) or {}, parcial=True)
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400
    sets = ", ".join(f"{k} = %({k})s" for k in c)
    c["id"] = rid
    try:
        fila = consulta(f"UPDATE resultados SET {sets} WHERE id = %(id)s RETURNING *", c, uno=True, commit=True)
    except psycopg2.errors.UniqueViolation:
        return jsonify(error="ya existe ese metodo_pago/dia_num"), 409
    return (jsonify(fila), 200) if fila else (jsonify(error="no existe"), 404)


@app.delete("/resultados/<int:rid>")
def borrar(rid):
    fila = consulta("DELETE FROM resultados WHERE id = %s RETURNING id", (rid,), uno=True, commit=True)
    return (jsonify(eliminado=fila["id"]), 200) if fila else (jsonify(error="no existe"), 404)
