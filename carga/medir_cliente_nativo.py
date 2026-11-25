"""
Verificação da "armadilha de medição": mede, com clientes Python nativos (sem o k6), a latência
sequencial (1 usuário) de REST e gRPC no cenário pesado (página de 1.000 músicas), nas duas linguagens.

Se o gRPC for mais rápido aqui do que no k6, o gargalo medido pelo k6 está no próprio gerador de carga
(conversão de protobuf para objetos JavaScript), e não no servidor.

Executar (na pasta python/, com os servidores no ar):  python ../carga/medir_cliente_nativo.py
"""
import os
import random
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python", "grpc_svc"))
import grpc  # noqa: E402
import requests  # noqa: E402
import streaming_pb2 as pb  # noqa: E402
import streaming_pb2_grpc as pb_grpc  # noqa: E402

N = int(os.environ.get("N", 300))
PORTAS = {"python": (8001, 50051), "node": (9001, 50052)}


def medir(fn):
    for _ in range(20):          # aquecimento
        fn(random.randint(1, 100))
    t = []
    for _ in range(N):
        p = random.randint(1, 100)
        t0 = time.perf_counter()
        fn(p)
        t.append((time.perf_counter() - t0) * 1000)
    return statistics.median(t)


for ling in sys.argv[1:] or ["python", "node"]:
    pr, pg = PORTAS[ling]
    s = requests.Session()
    stub = pb_grpc.StreamingStub(grpc.insecure_channel(f"localhost:{pg}"))
    rest = medir(lambda p: s.get(f"http://localhost:{pr}/musicas?pagina={p}&tamanho=1000").json())
    grp = medir(lambda p: list(stub.ListarMusicas(pb.Pagina(pagina=p, tamanho=1000)).musicas))
    print(f"{ling}: mediana com cliente nativo, 1.000 músicas -> REST {rest:.2f} ms | gRPC {grp:.2f} ms")
