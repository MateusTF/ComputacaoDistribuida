"""
Serviço de streaming de músicas — gRPC (Python + grpcio + Protocol Buffers).

Contrato em ../contratos/streaming.proto; stubs gerados pelo protoc.
Mensagens binárias (protobuf) trafegam sobre HTTP/2.

Executar (na pasta python/):  python -m grpc_svc.servidor        (porta 50051)
"""
import os
import sys
from concurrent import futures

import grpc

sys.path.insert(0, os.path.dirname(__file__))  # o código gerado usa import absoluto
import streaming_pb2 as pb  # noqa: E402
import streaming_pb2_grpc as pb_grpc  # noqa: E402

from comum.dados import ErroNaoEncontrado, ErroValidacao, novo_repositorio  # noqa: E402

repo = novo_repositorio()


def _u(u): return pb.Usuario(id=u.id, nome=u.nome, idade=u.idade)
def _m(m): return pb.Musica(id=m.id, nome=m.nome, duracao_seg=m.duracao_seg, album_id=m.album_id, genero_id=m.genero_id)
def _p(p): return pb.Playlist(id=p.id, nome=p.nome, usuario_id=p.usuario_id, musicas=p.musicas)
def _g(g): return pb.Genero(id=g.id, nome=g.nome)
def _ar(a): return pb.Artista(id=a.id, nome=a.nome, pais=a.pais)
def _al(a): return pb.Album(id=a.id, titulo=a.titulo, ano=a.ano, artista_id=a.artista_id)
def _opc(req, campo): return getattr(req, campo) if req.HasField(campo) else None


def tratar_erros(fn):
    """Converte exceções do domínio em códigos de status gRPC."""
    def wrapper(self, request, context):
        try:
            return fn(self, request, context)
        except ErroNaoEncontrado as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except ErroValidacao as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
    return wrapper


class StreamingServicer(pb_grpc.StreamingServicer):
    # ---------- usuários ----------
    @tratar_erros
    def ListarUsuarios(self, req, ctx):
        return pb.Usuarios(usuarios=[_u(u) for u in repo.listar_usuarios(req.pagina, req.tamanho)])

    @tratar_erros
    def ObterUsuario(self, req, ctx):
        return _u(repo.obter_usuario(req.id))

    @tratar_erros
    def CriarUsuario(self, req, ctx):
        return _u(repo.criar_usuario(req.nome, req.idade))

    @tratar_erros
    def AtualizarUsuario(self, req, ctx):
        return _u(repo.atualizar_usuario(req.id, _opc(req, "nome"), _opc(req, "idade")))

    @tratar_erros
    def RemoverUsuario(self, req, ctx):
        repo.remover_usuario(req.id)
        return pb.Vazio()

    # ---------- músicas ----------
    @tratar_erros
    def ListarMusicas(self, req, ctx):
        return pb.Musicas(musicas=[_m(m) for m in repo.listar_musicas(req.pagina, req.tamanho)])

    @tratar_erros
    def ObterMusica(self, req, ctx):
        return _m(repo.obter_musica(req.id))

    @tratar_erros
    def CriarMusica(self, req, ctx):
        return _m(repo.criar_musica(req.nome, req.duracao_seg, req.album_id, req.genero_id))

    @tratar_erros
    def AtualizarMusica(self, req, ctx):
        return _m(repo.atualizar_musica(req.id, _opc(req, "nome"), _opc(req, "duracao_seg"),
                                        _opc(req, "album_id"), _opc(req, "genero_id")))

    @tratar_erros
    def RemoverMusica(self, req, ctx):
        repo.remover_musica(req.id)
        return pb.Vazio()

    # ---------- playlists ----------
    @tratar_erros
    def ListarPlaylists(self, req, ctx):
        return pb.Playlists(playlists=[_p(p) for p in repo.listar_playlists(req.pagina, req.tamanho)])

    @tratar_erros
    def ObterPlaylist(self, req, ctx):
        return _p(repo.obter_playlist(req.id))

    @tratar_erros
    def CriarPlaylist(self, req, ctx):
        return _p(repo.criar_playlist(req.nome, req.usuario_id, list(req.musicas)))

    @tratar_erros
    def AtualizarPlaylist(self, req, ctx):
        return _p(repo.atualizar_playlist(req.id, _opc(req, "nome"),
                                          list(req.musicas) if req.trocar_musicas else None))

    @tratar_erros
    def RemoverPlaylist(self, req, ctx):
        repo.remover_playlist(req.id)
        return pb.Vazio()

    # ---------- consultas do enunciado ----------
    @tratar_erros
    def PlaylistsDoUsuario(self, req, ctx):
        return pb.Playlists(playlists=[_p(p) for p in repo.playlists_do_usuario(req.id)])

    @tratar_erros
    def MusicasDaPlaylist(self, req, ctx):
        return pb.Musicas(musicas=[_m(m) for m in repo.musicas_da_playlist(req.id)])

    @tratar_erros
    def PlaylistsComMusica(self, req, ctx):
        return pb.Playlists(playlists=[_p(p) for p in repo.playlists_com_musica(req.id)])

    # ---------- entidades extras ----------
    @tratar_erros
    def ListarGeneros(self, req, ctx):
        return pb.Generos(generos=[_g(g) for g in repo.listar_generos()])

    @tratar_erros
    def ObterGenero(self, req, ctx):
        return _g(repo.obter_genero(req.id))

    @tratar_erros
    def ListarArtistas(self, req, ctx):
        return pb.Artistas(artistas=[_ar(a) for a in repo.listar_artistas(req.pagina, req.tamanho)])

    @tratar_erros
    def ObterArtista(self, req, ctx):
        return _ar(repo.obter_artista(req.id))

    @tratar_erros
    def AlbunsDoArtista(self, req, ctx):
        return pb.Albuns(albuns=[_al(a) for a in repo.albuns_do_artista(req.id)])

    @tratar_erros
    def ObterAlbum(self, req, ctx):
        return _al(repo.obter_album(req.id))

    @tratar_erros
    def MusicasDoAlbum(self, req, ctx):
        return pb.Musicas(musicas=[_m(m) for m in repo.musicas_do_album(req.id)])

    # ---------- server streaming ----------
    def TransmitirMusicasDaPlaylist(self, req, ctx):
        try:
            musicas = repo.musicas_da_playlist(req.id)
        except ErroNaoEncontrado as e:
            ctx.abort(grpc.StatusCode.NOT_FOUND, str(e))
        for m in musicas:
            yield _m(m)


def servir(porta: int = int(os.environ.get("PORTA", 50051)), workers: int = 16):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=workers))
    pb_grpc.add_StreamingServicer_to_server(StreamingServicer(), server)
    server.add_insecure_port(f"[::]:{porta}")
    server.start()
    print(f"gRPC (Python) ouvindo na porta {porta}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    servir()
