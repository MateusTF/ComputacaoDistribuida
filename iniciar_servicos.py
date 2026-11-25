"""
Sobe os 8 serviços (4 em Python + 4 em Node.js) num único terminal, sem Docker.
Funciona no Windows, Mac e Linux. Ctrl+C encerra todos.

Pré-requisitos: banco no ar (ex.: docker compose up -d db), ambiente Python ativado com as
dependências instaladas (pip install -r python/requirements.txt) e npm install feito em node/.

Executar (na raiz do projeto):   python iniciar_servicos.py
Só uma linguagem:                python iniciar_servicos.py python      (ou: node)
"""
import os
import shutil
import socket
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable  # o Python que está rodando este script (o do ambiente .venv, se ativado)

SERVICOS = {
    "python": [
        ("REST    Python  :8001 ", [PY, "-m", "uvicorn", "rest.servidor:app", "--port", "8001", "--log-level", "warning"]),
        ("GraphQL Python  :8002 ", [PY, "-m", "uvicorn", "graphql_svc.servidor:app", "--port", "8002", "--log-level", "warning"]),
        ("SOAP    Python  :8003 ", [PY, "-m", "uvicorn", "soap.servidor:app", "--port", "8003", "--log-level", "warning"]),
        ("gRPC    Python  :50051", [PY, "-m", "grpc_svc.servidor"]),
    ],
    "node": [
        ("REST    Node.js :9001 ", ["node", "src/rest.ts"]),
        ("GraphQL Node.js :9002 ", ["node", "src/graphql.ts"]),
        ("SOAP    Node.js :9003 ", ["node", "src/soap.ts"]),
        ("gRPC    Node.js :50052", ["node", "src/grpc.ts"]),
    ],
}

linguagens = sys.argv[1:] or ["python", "node"]
if "node" in linguagens and shutil.which("node") is None:
    sys.exit("Node.js não encontrado. Instale o Node 22 (nodejs.org) ou rode só:  python iniciar_servicos.py python")

processos = []
for ling in linguagens:
    pasta = os.path.join(RAIZ, ling)
    for nome, cmd in SERVICOS[ling]:
        processos.append((nome, subprocess.Popen(cmd, cwd=pasta)))
        print(f"iniciado: {nome}")

def porta_aberta(nome):
    porta = int(nome.split(":")[1])
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", porta)) == 0


limite = time.time() + 30          # espera até 30 s: cada serviço precisa abrir a porta ou encerrar
while time.time() < limite:
    pendentes = [n for n, p in processos if p.poll() is None and not porta_aberta(n)]
    if not pendentes:
        break
    time.sleep(1)
mortos = [nome.strip() for nome, p in processos if p.poll() is not None]
lentos = [nome.strip() for nome, p in processos if p.poll() is None and not porta_aberta(nome)]
if mortos or lentos:
    if mortos:
        print("\nATENÇÃO: estes serviços pararam ao iniciar (veja o erro acima):\n  " + "\n  ".join(mortos))
    if lentos:
        print("\nATENÇÃO: estes serviços ainda não responderam:\n  " + "\n  ".join(lentos))
    print("Causas comuns: banco fora do ar, dependências não instaladas ou porta já em uso.")
else:
    print(f"\n{len(processos)} serviços no ar. Teste em outro terminal:  cd python  e  python -m clientes.teste_funcional")
print("Ctrl+C para encerrar todos.\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nEncerrando...")
    for _, p in processos:
        p.terminate()
    for _, p in processos:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
