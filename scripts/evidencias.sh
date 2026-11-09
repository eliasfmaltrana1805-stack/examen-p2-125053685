#!/usr/bin/env bash
# Ejecuta todas las verificaciones y guarda los logs en evidencias/. Uso: ./scripts/evidencias.sh
set -uo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
E=evidencias; mkdir -p $E
H="docker compose exec -T -u hadoop hadoop"
CSV=/data/input/ventas_${MATRICULA}.csv
$H hadoop version                                         | tee $E/hadoop_version.txt
{ $H ssh localhost 'echo "ssh localhost OK en $(hostname)"'
  docker compose exec -T api ssh hadoop 'echo "api -> hadoop OK en $(hostname)"'; } 2>&1 | tee $E/ssh.txt
{ time $H /opt/mapreduce/run_job.sh; } 2>&1 | tee $E/job_log.txt
$H cat /data/output/resultado/part-00000                  | tee $E/job_output.txt
{ time $H python3 /opt/mapreduce/secuencial.py $CSV /tmp/seq.txt; } 2>&1 | tee $E/secuencial_log.txt
$H diff /tmp/seq.txt /data/output/resultado/part-00000 && echo "RESULTADOS IGUALES" | tee $E/comparacion.txt
docker compose exec -T api python scripts/cargar_resultados.py | tee $E/carga.txt
P=${API_PORT:-5000}
{ curl -s localhost:$P/resultados; echo; curl -s localhost:$P/resultados/Efectivo; echo
  curl -s "localhost:$P/resultados/Tarjeta?dia=3"; echo
  curl -s -X POST localhost:$P/resultados -H 'Content-Type: application/json' -d '{"metodo_pago":"Cripto","dia_num":1,"unidades_vendidas":10}'; echo
  curl -s -X PUT localhost:$P/resultados/29 -H 'Content-Type: application/json' -d '{"unidades_vendidas":99}'; echo
  curl -s -X DELETE localhost:$P/resultados/29; echo; } | tee $E/api.txt
{ docker compose down; docker compose up -d; sleep 15; curl -s localhost:$P/resultados | head -c 400; echo; } 2>&1 | tee $E/persistencia.txt
