"""
Verifica que as 8 implementações (Python e Node.js × REST, GraphQL, gRPC e SOAP) respondem às
5 consultas do enunciado com os MESMOS dados e que o CRUD funciona em todas.

Executar (na pasta python/), com o banco e os 8 servidores no ar:
    python -m clientes.teste_funcional              # testa as duas linguagens
    python -m clientes.teste_funcional python       # só uma linguagem
"""
import sys

from clientes.clientes import cliente

linguagens = sys.argv[1:] or ["python", "node"]
tecnologias = ["rest", "graphql", "grpc", "soap"]
NOMES = {"rest": "REST", "graphql": "GraphQL", "grpc": "gRPC", "soap": "SOAP", "python": "Python", "node": "Node.js"}
clientes = {(l, t): cliente(l, t) for l in linguagens for t in tecnologias}


def normalizar(lista):
    norm = []
    for item in lista:
        d = {k: v for k, v in dict(item).items()}
        for camel, snake in (("usuarioId", "usuario_id"), ("duracaoSeg", "duracao_seg"),
                             ("albumId", "album_id"), ("generoId", "genero_id"), ("artistaId", "artista_id")):
            if camel in d:
                d[snake] = d.pop(camel)
        norm.append(d)
    return sorted(norm, key=lambda d: d["id"])


consultas = {
    "1. Usuários (1ª página)":          lambda c: c.listar_usuarios(),
    "2. Músicas (1ª página)":           lambda c: c.listar_musicas(),
    "3. Playlists do usuário 7":        lambda c: c.playlists_do_usuario(7),
    "4. Músicas da playlist 5":         lambda c: c.musicas_da_playlist(5),
    "5. Playlists com a música 42":     lambda c: c.playlists_com_musica(42),
    "6. Álbuns do artista 3 (extra)":   lambda c: c.albuns_do_artista(3),
}

print(f"Comparando {len(clientes)} serviços: " + ", ".join(f"{NOMES[t]} ({NOMES[l]})" for l, t in clientes))
falhas = 0
for nome, consulta in consultas.items():
    resultados = {k: normalizar(consulta(c)) for k, c in clientes.items()}
    referencia = next(iter(resultados.values()))
    iguais = all(r == referencia for r in resultados.values())
    falhas += not iguais
    print(f"{'OK ' if iguais else 'ERRO'} {nome}: {len(referencia)} itens "
          f"{'(idênticos nos ' + str(len(clientes)) + ' serviços)' if iguais else {k: len(r) for k, r in resultados.items()}}")

print("\nCRUD:")
for (l, t), c in clientes.items():
    rotulo = f"{NOMES[t]} ({NOMES[l]})"
    u = c.criar_usuario(f"Teste {rotulo}", 21)                                  # Create
    p = c.criar_playlist(f"Favoritas {rotulo}", u["id"], [1, 2, 3])             # Create (relacionamento)
    assert normalizar(c.playlists_do_usuario(u["id"]))[0]["id"] == p["id"]      # Read
    u2 = c.atualizar_usuario(u["id"], f"Teste {rotulo} (alterado)")             # Update
    assert u2["nome"].endswith("(alterado)") and u2["idade"] == 21
    c.remover_usuario(u["id"])                                                  # Delete
    try:
        c.obter_usuario(u["id"])                                                # tem que falhar
        print(f"ERRO {rotulo}: usuário removido ainda existe"); falhas += 1
    except Exception as e:
        print(f"OK  {rotulo}: criar/consultar/alterar/remover; erro esperado após remoção -> {type(e).__name__}")

for l in linguagens:
    n = len(clientes[(l, "grpc")].transmitir_musicas(5))
    print(f"\ngRPC server streaming ({NOMES[l]}, playlist 5): {n} músicas recebidas", end="")
print("\n\nRESULTADO:", "tudo certo" if not falhas else f"{falhas} falha(s)")
sys.exit(1 if falhas else 0)
