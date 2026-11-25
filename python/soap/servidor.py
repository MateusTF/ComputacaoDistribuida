"""
Serviço de streaming de músicas — SOAP 1.1 (Python + Spyne).

Operações expostas como chamadas de procedimento; mensagens em envelopes XML; o contrato
(WSDL) é gerado a partir destas classes. Ele foi exportado para contratos/streaming.wsdl e é o
mesmo contrato usado pela versão Node.js.  WSDL ao vivo: http://localhost:8003/?wsdl

Executar (na pasta python/):  uvicorn soap.servidor:app --port 8003
"""
from a2wsgi import WSGIMiddleware
from spyne import (Application, Array, ComplexModel, Integer, Iterable, ServiceBase,
                   Unicode, rpc)
from spyne.error import ResourceNotFoundError, ValidationError
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from comum.dados import ErroNaoEncontrado, ErroValidacao, novo_repositorio

repo = novo_repositorio()
NS = "urn:unifor:streaming"


# ---------- tipos complexos (viram xsd:complexType no WSDL) ----------
class Usuario(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode
    idade = Integer


class Musica(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode
    duracao_seg = Integer
    album_id = Integer
    genero_id = Integer


class Playlist(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode
    usuario_id = Integer
    musicas = Array(Integer)


class Genero(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode


class Artista(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode
    pais = Unicode


class Album(ComplexModel):
    __namespace__ = NS
    id = Integer
    titulo = Unicode
    ano = Integer
    artista_id = Integer


def _u(u): return Usuario(id=u.id, nome=u.nome, idade=u.idade)
def _m(m): return Musica(id=m.id, nome=m.nome, duracao_seg=m.duracao_seg, album_id=m.album_id, genero_id=m.genero_id)
def _p(p): return Playlist(id=p.id, nome=p.nome, usuario_id=p.usuario_id, musicas=p.musicas)
def _g(g): return Genero(id=g.id, nome=g.nome)
def _ar(a): return Artista(id=a.id, nome=a.nome, pais=a.pais)
def _al(a): return Album(id=a.id, titulo=a.titulo, ano=a.ano, artista_id=a.artista_id)


def _executar(fn, *args):
    """Converte exceções do domínio em SOAP Faults."""
    try:
        return fn(*args)
    except ErroNaoEncontrado as e:
        raise ResourceNotFoundError(str(e))
    except ErroValidacao as e:
        raise ValidationError(str(e))


class StreamingService(ServiceBase):
    # ---------- usuários ----------
    @rpc(Integer, Integer, _returns=Iterable(Usuario))
    def ListarUsuarios(ctx, pagina, tamanho):
        return [_u(u) for u in repo.listar_usuarios(pagina, tamanho)]

    @rpc(Integer, _returns=Usuario)
    def ObterUsuario(ctx, id):
        return _u(_executar(repo.obter_usuario, id))

    @rpc(Unicode, Integer, _returns=Usuario)
    def CriarUsuario(ctx, nome, idade):
        return _u(repo.criar_usuario(nome, idade))

    @rpc(Integer, Unicode, Integer, _returns=Usuario)
    def AtualizarUsuario(ctx, id, nome, idade):
        return _u(_executar(repo.atualizar_usuario, id, nome, idade))

    @rpc(Integer)
    def RemoverUsuario(ctx, id):
        _executar(repo.remover_usuario, id)

    # ---------- músicas ----------
    @rpc(Integer, Integer, _returns=Iterable(Musica))
    def ListarMusicas(ctx, pagina, tamanho):
        return [_m(m) for m in repo.listar_musicas(pagina, tamanho)]

    @rpc(Integer, _returns=Musica)
    def ObterMusica(ctx, id):
        return _m(_executar(repo.obter_musica, id))

    @rpc(Unicode, Integer, Integer, Integer, _returns=Musica)
    def CriarMusica(ctx, nome, duracao_seg, album_id, genero_id):
        return _m(_executar(repo.criar_musica, nome, duracao_seg, album_id, genero_id))

    @rpc(Integer, Unicode, Integer, Integer, Integer, _returns=Musica)
    def AtualizarMusica(ctx, id, nome, duracao_seg, album_id, genero_id):
        return _m(_executar(repo.atualizar_musica, id, nome, duracao_seg, album_id, genero_id))

    @rpc(Integer)
    def RemoverMusica(ctx, id):
        _executar(repo.remover_musica, id)

    # ---------- playlists ----------
    @rpc(Integer, Integer, _returns=Iterable(Playlist))
    def ListarPlaylists(ctx, pagina, tamanho):
        return [_p(p) for p in repo.listar_playlists(pagina, tamanho)]

    @rpc(Integer, _returns=Playlist)
    def ObterPlaylist(ctx, id):
        return _p(_executar(repo.obter_playlist, id))

    @rpc(Unicode, Integer, Array(Integer), _returns=Playlist)
    def CriarPlaylist(ctx, nome, usuario_id, musicas):
        return _p(_executar(repo.criar_playlist, nome, usuario_id, list(musicas or [])))

    @rpc(Integer, Unicode, Array(Integer), _returns=Playlist)
    def AtualizarPlaylist(ctx, id, nome, musicas):
        return _p(_executar(repo.atualizar_playlist, id, nome,
                            list(musicas) if musicas is not None else None))

    @rpc(Integer)
    def RemoverPlaylist(ctx, id):
        _executar(repo.remover_playlist, id)

    # ---------- consultas do enunciado ----------
    @rpc(Integer, _returns=Iterable(Playlist))
    def PlaylistsDoUsuario(ctx, id):
        return [_p(p) for p in _executar(repo.playlists_do_usuario, id)]

    @rpc(Integer, _returns=Iterable(Musica))
    def MusicasDaPlaylist(ctx, id):
        return [_m(m) for m in _executar(repo.musicas_da_playlist, id)]

    @rpc(Integer, _returns=Iterable(Playlist))
    def PlaylistsComMusica(ctx, id):
        return [_p(p) for p in _executar(repo.playlists_com_musica, id)]

    # ---------- entidades extras ----------
    @rpc(_returns=Iterable(Genero))
    def ListarGeneros(ctx):
        return [_g(g) for g in repo.listar_generos()]

    @rpc(Integer, _returns=Genero)
    def ObterGenero(ctx, id):
        return _g(_executar(repo.obter_genero, id))

    @rpc(Integer, Integer, _returns=Iterable(Artista))
    def ListarArtistas(ctx, pagina, tamanho):
        return [_ar(a) for a in repo.listar_artistas(pagina, tamanho)]

    @rpc(Integer, _returns=Artista)
    def ObterArtista(ctx, id):
        return _ar(_executar(repo.obter_artista, id))

    @rpc(Integer, _returns=Iterable(Album))
    def AlbunsDoArtista(ctx, id):
        return [_al(a) for a in _executar(repo.albuns_do_artista, id)]

    @rpc(Integer, _returns=Album)
    def ObterAlbum(ctx, id):
        return _al(_executar(repo.obter_album, id))

    @rpc(Integer, _returns=Iterable(Musica))
    def MusicasDoAlbum(ctx, id):
        return [_m(m) for m in _executar(repo.musicas_do_album, id)]


aplicacao = Application([StreamingService], tns=NS,
                        in_protocol=Soap11(validator="lxml"),
                        out_protocol=Soap11())
wsgi_app = WsgiApplication(aplicacao)
app = WSGIMiddleware(wsgi_app, workers=16)  # roda no mesmo servidor (uvicorn) que REST e GraphQL
