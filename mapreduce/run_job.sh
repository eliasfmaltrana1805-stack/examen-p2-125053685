#!/usr/bin/env bash
# Ejecuta el job de Hadoop Streaming (C1). Uso (dentro del contenedor hadoop): ./run_job.sh [csv]
set -euo pipefail
CSV="${1:-$(ls /data/input/ventas_*.csv | head -1)}"
OUT=/data/output/resultado
rm -rf "$OUT"                                   # Hadoop exige que el directorio de salida no exista
cd /opt/mapreduce
hadoop jar "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.local.map.tasks.maximum=4 \
  -D mapreduce.job.reduces=1 \
  -input "$CSV" \
  -output "$OUT" \
  -mapper mapper.py -reducer reducer.py -combiner reducer.py \
  -file mapper.py -file reducer.py
