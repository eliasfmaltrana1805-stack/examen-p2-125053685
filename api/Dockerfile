FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/app.py api/entrypoint.sh ./
COPY scripts/cargar_resultados.py scripts/
RUN chmod +x entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "2", "app:app"]
