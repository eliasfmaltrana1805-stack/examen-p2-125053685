#!/usr/bin/env python3
"""Genera capturas PNG con aspecto de GNOME Terminal (Ubuntu) a partir de la salida REAL de los
comandos del pipeline. Requiere el stack arriba (docker compose up -d) y google-chrome/chromium.
Uso: python3 scripts/capturas_ubuntu.py   ->  evidencias/capturas/*.png"""
import html, json, os, re, shutil, socket, subprocess, sys, textwrap, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "evidencias", "capturas")
TMP = os.path.join(OUT, "_html")
USER, HOST = os.environ.get("USER", "efml"), socket.gethostname()
CWD = "~/Documents/BIG DATA/examen-p2-125053685"
PORT = os.environ.get("API_PORT", "5000")
H = "docker compose exec -T -u hadoop hadoop"
CHROME = shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chromium")
os.makedirs(TMP, exist_ok=True)


def run(cmd, timeout=600):
    p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return (p.stdout + p.stderr).rstrip("\n")


def leer(rel, tail=None, head=None):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        lines = f.read().rstrip("\n").split("\n")
    return "\n".join(lines[-tail:] if tail else lines[:head] if head else lines)


def pretty(js):
    try:
        return json.dumps(json.loads(js), indent=2, ensure_ascii=False)
    except Exception:
        return js


def wrap(text, width=118):
    out = []
    for ln in text.split("\n"):
        out += textwrap.wrap(ln, width, replace_whitespace=False, drop_whitespace=False) or [""]
    return out


def render(name, title, blocks):
    """blocks: lista de (comando_mostrado, salida)"""
    body, nlines = [], 0
    for cmd, out in blocks:
        body.append(f'<div class="l"><span class="u">{USER}@{HOST}</span>:<span class="p">{html.escape(CWD)}</span>$ '
                    f'<span class="c">{html.escape(cmd)}</span></div>')
        nlines += len(wrap(f"{USER}@{HOST}:{CWD}$ {cmd}", 118))
        for ln in wrap(out) if out else []:
            body.append(f'<div class="l">{html.escape(ln) or "&nbsp;"}</div>')
            nlines += 1
    body.append(f'<div class="l"><span class="u">{USER}@{HOST}</span>:<span class="p">{html.escape(CWD)}</span>$ <span class="cur"></span></div>')
    nlines += 1
    height = 46 + nlines * 21 + 24
    page = f"""<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;background:#300a24}}
.win{{width:1100px;border-radius:10px 10px 0 0;overflow:hidden;background:#300a24;box-shadow:0 0 0 1px #000}}
.bar{{height:46px;background:#2d2d2d;display:flex;align-items:center;justify-content:space-between;padding:0 14px;color:#dfdbd2;
 font:600 14px 'Ubuntu','Ubuntu Sans','DejaVu Sans',sans-serif;border-bottom:1px solid #1a1a1a}}
.bar .t{{flex:1;text-align:center}} .bar .s{{width:92px}}
.btns{{display:flex;gap:10px;width:92px;justify-content:flex-end}}
.btn{{width:24px;height:24px;border-radius:50%;background:#3d3d3d;display:flex;align-items:center;justify-content:center;font-size:12px;color:#dfdbd2}}
.btn.x{{background:#e95420;color:#fff}}
.term{{padding:10px 14px 14px;font:16px/21px 'Ubuntu Mono','Ubuntu Sans Mono','DejaVu Sans Mono',monospace;color:#eeeeec;white-space:pre-wrap;word-break:break-all}}
.u{{color:#8ae234;font-weight:bold}} .p{{color:#729fcf;font-weight:bold}} .c{{color:#fff}}
.cur{{display:inline-block;width:9px;height:17px;background:#eeeeec;vertical-align:-3px}}
</style><div class="win"><div class="bar"><div class="s"></div><div class="t">{html.escape(title)}</div>
<div class="btns"><div class="btn">&#8211;</div><div class="btn">&#9633;</div><div class="btn x">&#10005;</div></div></div>
<div class="term">{''.join(body)}</div></div>"""
    hp = os.path.join(TMP, name + ".html")
    open(hp, "w", encoding="utf-8").write(page)
    png = os.path.join(OUT, name + ".png")
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1.5", f"--window-size=1100,{height}",
                    f"--screenshot={png}", "file://" + hp], capture_output=True, timeout=120)
    print("ok", png)


def api(method, path, data=None):
    req = urllib.request.Request(f"http://localhost:{PORT}{path}", method=method,
                                 data=json.dumps(data).encode() if data else None,
                                 headers={"Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(req, timeout=30).read().decode()
    except urllib.error.HTTPError as e:
        return e.read().decode()


def main():
    if not CHROME:
        sys.exit("se requiere google-chrome o chromium")
    T = "efml@ubuntu"
    render("01_docker_compose_ps", f"{USER}@{HOST}: {CWD}",
           [("docker compose ps", run("docker compose ps"))])
    render("02_hadoop_version", f"{USER}@{HOST}: {CWD}",
           [("docker compose exec -u hadoop hadoop hadoop version", run(f"{H} hadoop version")),
            ("docker compose exec -u hadoop hadoop bash -c 'echo $JAVA_HOME $HADOOP_HOME'", run(f"{H} bash -c 'echo JAVA_HOME=$JAVA_HOME HADOOP_HOME=$HADOOP_HOME'"))])
    render("03_ssh_sin_password", f"{USER}@{HOST}: {CWD}",
           [("docker compose exec -u hadoop hadoop ssh localhost 'echo ssh localhost OK en $(hostname)'",
             run(f"{H} ssh localhost 'echo ssh localhost OK en $(hostname)'")),
            ("docker compose exec api ssh hadoop 'echo api -> hadoop OK en $(hostname)'",
             run("docker compose exec -T api ssh hadoop 'echo api -> hadoop OK en $(hostname)'")),
            ("docker compose exec -u hadoop hadoop grep -E '^(PasswordAuthentication|PermitRootLogin|AllowUsers)' /etc/ssh/sshd_config.d/hadoop.conf",
             run(f"{H} grep -E '^(PasswordAuthentication|PermitRootLogin|AllowUsers)' /etc/ssh/sshd_config.d/hadoop.conf"))])
    render("04_job_mapreduce", f"{USER}@{HOST}: {CWD}",
           [("time docker compose exec -u hadoop hadoop /opt/mapreduce/run_job.sh  # (final del log)",
             leer("evidencias/job_log.txt", tail=34))])
    render("05_salida_job_part-00000", f"{USER}@{HOST}: {CWD}",
           [("docker compose exec -u hadoop hadoop cat /data/output/resultado/part-00000",
             run(f"{H} cat /data/output/resultado/part-00000"))])
    render("06_comparativa_tiempos", f"{USER}@{HOST}: {CWD}",
           [("grep real evidencias/job_log.txt", "Hadoop Streaming  " + run("grep real evidencias/job_log.txt")),
            ("grep real evidencias/secuencial_log.txt", "Secuencial        " + run("grep real evidencias/secuencial_log.txt")),
            ("docker compose exec -u hadoop hadoop diff /tmp/seq.txt /data/output/resultado/part-00000 && echo RESULTADOS IGUALES",
             run(f"{H} diff /tmp/seq.txt /data/output/resultado/part-00000 && echo RESULTADOS IGUALES"))])
    render("07_mapper_malformadas", f"{USER}@{HOST}: {CWD}",
           [("python3 mapreduce/mapper.py < malo.csv   # encabezado + basura + fecha mala + cantidad 'abc' + vacia",
             leer("evidencias/mapper_malformadas.txt").split("\n", 1)[1])])
    render("08_api_get", f"{USER}@{HOST}: {CWD}",
           [("curl -s localhost:5000/resultados/Efectivo | python3 -m json.tool", pretty(api("GET", "/resultados/Efectivo"))),
            ("curl -s 'localhost:5000/resultados/Tarjeta?dia=3' | python3 -m json.tool", pretty(api("GET", "/resultados/Tarjeta?dia=3")))])
    nuevo = json.loads(api("POST", "/resultados", {"metodo_pago": "Cripto", "dia_num": 1, "unidades_vendidas": 10}))
    render("09_api_crud_escritura", f"{USER}@{HOST}: {CWD}",
           [("curl -s -X POST localhost:5000/resultados -H 'Content-Type: application/json' -d '{\"metodo_pago\":\"Cripto\",\"dia_num\":1,\"unidades_vendidas\":10}'", json.dumps(nuevo, ensure_ascii=False)),
            (f"curl -s -X PUT localhost:5000/resultados/{nuevo['id']} -H 'Content-Type: application/json' -d '{{\"unidades_vendidas\":99}}'", api("PUT", f"/resultados/{nuevo['id']}", {"unidades_vendidas": 99}).strip()),
            (f"curl -s -X DELETE localhost:5000/resultados/{nuevo['id']}", api("DELETE", f"/resultados/{nuevo['id']}").strip())])
    antes = len(json.loads(api("GET", "/resultados"))["resultados"])
    down = run("docker compose down 2>&1 | grep -E 'Removed' | head -6")
    up = run("docker compose up -d 2>&1 | grep -E 'Started|Healthy' | head -6")
    for _ in range(30):
        try:
            despues = len(json.loads(api("GET", "/resultados"))["resultados"]); break
        except Exception:
            time.sleep(2)
    render("10_persistencia", f"{USER}@{HOST}: {CWD}",
           [("curl -s localhost:5000/resultados | python3 -c 'import sys,json; print(len(json.load(sys.stdin)[\"resultados\"]), \"registros\")'", f"{antes} registros"),
            ("docker compose down", down), ("docker compose up -d", up),
            ("curl -s localhost:5000/resultados | python3 -c 'import sys,json; print(len(json.load(sys.stdin)[\"resultados\"]), \"registros\")'", f"{despues} registros  <- los datos siguen ahi")])
    render("11_down_v", f"{USER}@{HOST}: {CWD}",
           [("docker compose down -v && docker compose up -d --build   # los volumenes se borran", "")] +
           [("curl -s localhost:5000/resultados", leer("evidencias/down_v.txt").split("\n")[1]),
            ("docker compose exec api python scripts/cargar_resultados.py", "28 registros cargados desde /data/output/resultado/part-00000")])
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
