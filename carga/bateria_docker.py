"""
Bateria de testes de carga usando o Docker (funciona no Windows, Mac e Linux).

Pré-requisito: os serviços no ar com  docker compose up -d --build
Executar (na raiz do projeto):       python carga/bateria_docker.py
Depois, para gerar os gráficos:       python carga/analise.py

Opções (variáveis de ambiente, como no executar_testes.sh):
  LINGS="python node"  TECS="rest graphql grpc soap"  CENARIOS="leve pesado aninhado escrita"
  CARGAS="1 10 50 100 200"  DUR=20s
Exemplo rápido (PowerShell):  $env:CARGAS="1 200"; $env:DUR="10s"; python carga/bateria_docker.py
Só mostrar os comandos, sem executar:  python carga/bateria_docker.py --mostrar

Diferença em relação ao executar_testes.sh (Linux): aqui os 8 serviços ficam ligados ao mesmo
tempo e não há separação de núcleos da CPU. Os números absolutos podem variar mais; para comparar
com justiça, feche outros programas pesados enquanto a bateria roda.
"""
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOSTRAR = "--mostrar" in sys.argv

LINGS = os.environ.get("LINGS", "python node").split()
TECS = os.environ.get("TECS", "rest graphql grpc soap").split()
CENARIOS = os.environ.get("CENARIOS", "leve pesado aninhado escrita").split()
CARGAS = os.environ.get("CARGAS", "1 10 50 100 200").split()
DUR = os.environ.get("DUR", "20s")


def rodar(cmd, silencioso=False):
    if MOSTRAR:
        print("  $", " ".join(cmd))
        return 0
    saida = subprocess.DEVNULL if silencioso else None
    return subprocess.run(cmd, cwd=RAIZ, stdout=saida, stderr=saida).returncode


def k6(ling, tec, cen, vus, dur, arquivo=None):
    cmd = ["docker", "compose", "run", "--rm", "k6", "run", "-q",
           "-e", f"LING={ling}", "-e", f"TEC={tec}", "-e", f"CEN={cen}", "-e", f"VUS={vus}", "-e", f"DUR={dur}"]
    if arquivo:
        cmd += ["--summary-export", f"/carga/resultados/{arquivo}"]
    cmd.append("/carga/teste_carga.js")
    return rodar(cmd, silencioso=True)


def limpar_escritas():
    """Remove as playlists criadas no cenário de escrita, para não afetar os próximos testes."""
    for sql in ("DELETE FROM playlists WHERE id > 30000", "DELETE FROM usuarios WHERE id > 10000",
                "VACUUM ANALYZE playlists, playlist_musica"):
        rodar(["docker", "compose", "exec", "-T", "db", "psql", "-q", "-U", "streaming", "-d", "streaming", "-c", sql],
              silencioso=True)


os.makedirs(os.path.join(RAIZ, "carga", "resultados"), exist_ok=True)
total = len(LINGS) * len(TECS) * len(CENARIOS) * len(CARGAS)
print(f"{total} execuções de {DUR} (+ aquecimento). Tempo estimado: ~{total * 25 // 60} min\n")

feitos, falhas = 0, 0
limpar_escritas()
for ling in LINGS:
    for tec in TECS:
        for cen in CENARIOS:
            k6(ling, tec, cen, 5, "3s")                     # aquecimento (não é medido)
            for vus in CARGAS:
                feitos += 1
                print(f"[{feitos}/{total}] {time.strftime('%H:%M:%S')}  {ling:6} {tec:8} {cen:9} {vus:>3} usuários")
                if k6(ling, tec, cen, vus, DUR, f"{ling}_{tec}_{cen}_{vus}.json") != 0:
                    falhas += 1
                    print("    ! o k6 terminou com erro (o serviço está no ar? veja: docker compose ps)")
            if cen == "escrita":
                limpar_escritas()

print(f"\nFIM. {feitos - falhas} execuções concluídas, {falhas} com erro.")
print("Agora gere os gráficos com:  python carga/analise.py")
