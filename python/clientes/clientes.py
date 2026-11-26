"""
Clientes das 4 tecnologias com a MESMA interface. Cada cliente recebe o endereço do servidor,
então o mesmo código testa tanto a versão Python quanto a versão Node.js de cada tecnologia.
"""
import os
import sys

import grpc
import requests
import zeep

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "grpc_svc"))
import streaming_pb2 as pb  # noqa: E402
import streaming_pb2_grpc as pb_grpc  # noqa: E402

# endereços padrão de cada linguagem (mesmos do docker-compose.yml)
HOST = os.environ.get("HOST_SERVICOS", "localhost")
ENDERECOS = {
    "python": {"rest": f"http://{HOST}:8001", "graphql": f"http://{HOST}:8002/graphql",
               "soap": f"http://{HOST}:8003/?wsdl", "grpc": f"{HOST}:50051"},
    "node":   {"rest": f"http://{HOST}:9001", "graphql": f"http://{HOST}:9002/graphql",
               "soap": f"http://{HOST}:9003/?wsdl", "grpc": f"{HOST}:50052"},
}


# ======================= REST =======================
class ClienteREST:
    def __init__(self, url):
        self.url, self.s = url, requests.Session()

    def _ok(self, r):
        r.raise_for_status()
        return r.json() if r.content else None

    def listar_usuarios(self):          return self._ok(self.s.get(f"{self.url}/usuarios"))
    def listar_musicas(self):           return self._ok(self.s.get(f"{self.url}/musicas"))
    def playlists_do_usuario(self, id): return self._ok(self.s.get(f"{self.url}/usuarios/{id}/playlists"))
    def musicas_da_playlist(self, id):  return self._ok(self.s.get(f"{self.url}/playlists/{id}/musicas"))
    def playlists_com_musica(self, id): return self._ok(self.s.get(f"{self.url}/musicas/{id}/playlists"))
    def albuns_do_artista(self, id):    return self._ok(self.s.get(f"{self.url}/artistas/{id}/albuns"))

    def criar_usuario(self, nome, idade):
        return self._ok(self.s.post(f"{self.url}/usuarios", json={"nome": nome, "idade": idade}))
    def atualizar_usuario(self, id, nome):
        return self._ok(self.s.patch(f"{self.url}/usuarios/{id}", json={"nome": nome}))
    def remover_usuario(self, id):
        return self._ok(self.s.delete(f"{self.url}/usuarios/{id}"))
    def criar_playlist(self, nome, usuario_id, musicas):
        return self._ok(self.s.post(f"{self.url}/usuarios/{usuario_id}/playlists",
                                    json={"nome": nome, "musicas": musicas}))
    def obter_usuario(self, id):
        return self._ok(self.s.get(f"{self.url}/usuarios/{id}"))


# ======================= GraphQL =======================
P_CAMPOS = "id nome usuarioId musicas { id }"
M_CAMPOS = "id nome duracaoSeg albumId generoId"


class ClienteGraphQL:
    def __init__(self, url):
        self.url, self.s = url, requests.Session()

    def _q(self, query, **variaveis):
        r = self.s.post(self.url, json={"query": query, "variables": variaveis})
        r.raise_for_status()
        corpo = r.json()
        if corpo.get("errors"):
            raise RuntimeError(corpo["errors"][0]["message"])
        return next(iter(corpo["data"].values()))

    @staticmethod
    def _pl(ps):
        return [{**p, "musicas": [m["id"] for m in p["musicas"]]} for p in ps]

    def listar_usuarios(self):
        return self._q("{ usuarios { id nome idade } }")
    def listar_musicas(self):
        return self._q(f"{{ musicas {{ {M_CAMPOS} }} }}")
    def playlists_do_usuario(self, id):
        return self._pl(self._q(f"query($id:Int!){{ usuario(id:$id){{ playlists {{ {P_CAMPOS} }} }} }}", id=id)["playlists"])
    def musicas_da_playlist(self, id):
        return self._q(f"query($id:Int!){{ playlist(id:$id){{ musicas {{ {M_CAMPOS} }} }} }}", id=id)["musicas"]
    def playlists_com_musica(self, id):
        return self._pl(self._q(f"query($id:Int!){{ musica(id:$id){{ playlists {{ {P_CAMPOS} }} }} }}", id=id)["playlists"])
    def albuns_do_artista(self, id):
        return self._q("query($id:Int!){ artista(id:$id){ albuns { id titulo ano artistaId } } }", id=id)["albuns"]

    def criar_usuario(self, nome, idade):
        return self._q("mutation($n:String!,$i:Int!){ criarUsuario(nome:$n, idade:$i){ id nome idade } }", n=nome, i=idade)
    def atualizar_usuario(self, id, nome):
        return self._q("mutation($id:Int!,$n:String){ atualizarUsuario(id:$id, nome:$n){ id nome idade } }", id=id, n=nome)
    def remover_usuario(self, id):
        return self._q("mutation($id:Int!){ removerUsuario(id:$id) }", id=id)
    def criar_playlist(self, nome, usuario_id, musicas):
        return self._q("mutation($n:String!,$u:Int!,$m:[Int!]!){ criarPlaylist(nome:$n, usuarioId:$u, musicas:$m)"
                       "{ id nome usuarioId } }", n=nome, u=usuario_id, m=musicas)
    def obter_usuario(self, id):
        return self._q("query($id:Int!){ usuario(id:$id){ id nome idade } }", id=id)


# ======================= gRPC =======================
class ClienteGRPC:
    def __init__(self, alvo):
        self.stub = pb_grpc.StreamingStub(grpc.insecure_channel(alvo))

    @staticmethod
    def _p(p): return {"id": p.id, "nome": p.nome, "usuario_id": p.usuario_id, "musicas": list(p.musicas)}
    @staticmethod
    def _m(m): return {"id": m.id, "nome": m.nome, "duracao_seg": m.duracao_seg, "album_id": m.album_id,
                       "genero_id": m.genero_id}
    @staticmethod
    def _u(u): return {"id": u.id, "nome": u.nome, "idade": u.idade}

    def listar_usuarios(self):          return [self._u(u) for u in self.stub.ListarUsuarios(pb.Pagina()).usuarios]
    def listar_musicas(self):           return [self._m(m) for m in self.stub.ListarMusicas(pb.Pagina()).musicas]
    def playlists_do_usuario(self, id): return [self._p(p) for p in self.stub.PlaylistsDoUsuario(pb.Id(id=id)).playlists]
    def musicas_da_playlist(self, id):  return [self._m(m) for m in self.stub.MusicasDaPlaylist(pb.Id(id=id)).musicas]
    def playlists_com_musica(self, id): return [self._p(p) for p in self.stub.PlaylistsComMusica(pb.Id(id=id)).playlists]
    def albuns_do_artista(self, id):
        return [{"id": a.id, "titulo": a.titulo, "ano": a.ano, "artista_id": a.artista_id}
                for a in self.stub.AlbunsDoArtista(pb.Id(id=id)).albuns]

    def criar_usuario(self, nome, idade):
        return self._u(self.stub.CriarUsuario(pb.NovoUsuario(nome=nome, idade=idade)))
    def atualizar_usuario(self, id, nome):
        return self._u(self.stub.AtualizarUsuario(pb.AtualizaUsuario(id=id, nome=nome)))
    def remover_usuario(self, id):
        self.stub.RemoverUsuario(pb.Id(id=id))
    def criar_playlist(self, nome, usuario_id, musicas):
        return self._p(self.stub.CriarPlaylist(pb.NovaPlaylist(nome=nome, usuario_id=usuario_id, musicas=musicas)))
    def obter_usuario(self, id):
        return self._u(self.stub.ObterUsuario(pb.Id(id=id)))
    def transmitir_musicas(self, id):
        return [self._m(m) for m in self.stub.TransmitirMusicasDaPlaylist(pb.Id(id=id))]


# ======================= SOAP =======================
class ClienteSOAP:
    def __init__(self, wsdl):
        # proxy gerado dinamicamente a partir do WSDL. O endereço das chamadas é o mesmo de onde o
        # WSDL foi baixado (e não o escrito dentro dele), para funcionar também dentro do Docker.
        cliente = zeep.Client(wsdl)
        self.svc = cliente.create_service("{urn:unifor:streaming}Application", wsdl.split("?")[0])

    @staticmethod
    def _lista(r):
        # Iterable(...) chega como um wrapper com um único campo contendo a lista
        if r is None:
            return []
        valores = list(r.__values__.values()) if hasattr(r, "__values__") else [r]
        return valores[0] or []

    @staticmethod
    def _p(p):
        ids = p.musicas.integer if p.musicas is not None else []
        return {"id": p.id, "nome": p.nome, "usuario_id": p.usuario_id, "musicas": list(ids)}
    @staticmethod
    def _m(m): return {"id": m.id, "nome": m.nome, "duracao_seg": m.duracao_seg, "album_id": m.album_id,
                       "genero_id": m.genero_id}
    @staticmethod
    def _u(u): return {"id": u.id, "nome": u.nome, "idade": u.idade}

    def listar_usuarios(self):          return [self._u(u) for u in self._lista(self.svc.ListarUsuarios())]
    def listar_musicas(self):           return [self._m(m) for m in self._lista(self.svc.ListarMusicas())]
    def playlists_do_usuario(self, id): return [self._p(p) for p in self._lista(self.svc.PlaylistsDoUsuario(id))]
    def musicas_da_playlist(self, id):  return [self._m(m) for m in self._lista(self.svc.MusicasDaPlaylist(id))]
    def playlists_com_musica(self, id): return [self._p(p) for p in self._lista(self.svc.PlaylistsComMusica(id))]
    def albuns_do_artista(self, id):
        return [{"id": a.id, "titulo": a.titulo, "ano": a.ano, "artista_id": a.artista_id}
                for a in self._lista(self.svc.AlbunsDoArtista(id))]

    def criar_usuario(self, nome, idade):  return self._u(self.svc.CriarUsuario(nome, idade))
    def atualizar_usuario(self, id, nome): return self._u(self.svc.AtualizarUsuario(id, nome))
    def remover_usuario(self, id):         self.svc.RemoverUsuario(id)
    def criar_playlist(self, nome, usuario_id, musicas):
        return self._p(self.svc.CriarPlaylist(nome, usuario_id, {"integer": musicas}))
    def obter_usuario(self, id):           return self._u(self.svc.ObterUsuario(id))


CLASSES = {"rest": ClienteREST, "graphql": ClienteGraphQL, "grpc": ClienteGRPC, "soap": ClienteSOAP}


def cliente(linguagem: str, tecnologia: str):
    return CLASSES[tecnologia](ENDERECOS[linguagem][tecnologia])
