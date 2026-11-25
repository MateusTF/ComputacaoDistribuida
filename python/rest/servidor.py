"""
Serviço de streaming de músicas — REST (Python + FastAPI).

Recursos identificados por URIs, verbos HTTP para o CRUD e JSON como representação.
Documentação OpenAPI gerada automaticamente em /docs.

Executar (na pasta python/):  uvicorn rest.servidor:app --port 8001
"""
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

from comum.dados import ErroNaoEncontrado, ErroValidacao, novo_repositorio

app = FastAPI(title="Streaming de Músicas — REST (Python)")
repo = novo_repositorio()


# ---------- representações ----------
class UsuarioIn(BaseModel):
    nome: str
    idade: int

class UsuarioPatch(BaseModel):
    nome: str | None = None
    idade: int | None = None

class Usuario(UsuarioIn):
    id: int

class MusicaIn(BaseModel):
    nome: str
    duracao_seg: int
    album_id: int
    genero_id: int

class MusicaPatch(BaseModel):
    nome: str | None = None
    duracao_seg: int | None = None
    album_id: int | None = None
    genero_id: int | None = None

class Musica(MusicaIn):
    id: int

class PlaylistIn(BaseModel):
    nome: str
    musicas: list[int]

class PlaylistPatch(BaseModel):
    nome: str | None = None
    musicas: list[int] | None = None

class Playlist(BaseModel):
    id: int
    nome: str
    usuario_id: int
    musicas: list[int]

class Genero(BaseModel):
    id: int
    nome: str

class Artista(BaseModel):
    id: int
    nome: str
    pais: str

class Album(BaseModel):
    id: int
    titulo: str
    ano: int
    artista_id: int


def _executar(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except ErroNaoEncontrado as e:
        raise HTTPException(404, str(e))
    except ErroValidacao as e:
        raise HTTPException(422, str(e))


PAG = Query(1, ge=1)
TAM = Query(100, ge=1, le=1000)


# ---------- /usuarios ----------
@app.get("/usuarios", response_model=list[Usuario])
def listar_usuarios(pagina: int = PAG, tamanho: int = TAM):
    return repo.listar_usuarios(pagina, tamanho)

@app.get("/usuarios/{id}", response_model=Usuario)
def obter_usuario(id: int):
    return _executar(repo.obter_usuario, id)

@app.post("/usuarios", response_model=Usuario, status_code=201)
def criar_usuario(u: UsuarioIn):
    return repo.criar_usuario(u.nome, u.idade)

@app.patch("/usuarios/{id}", response_model=Usuario)
def atualizar_usuario(id: int, u: UsuarioPatch):
    return _executar(repo.atualizar_usuario, id, u.nome, u.idade)

@app.delete("/usuarios/{id}", status_code=204)
def remover_usuario(id: int):
    _executar(repo.remover_usuario, id)
    return Response(status_code=204)

@app.get("/usuarios/{id}/playlists", response_model=list[Playlist])      # consulta do enunciado
def playlists_do_usuario(id: int):
    return _executar(repo.playlists_do_usuario, id)

@app.post("/usuarios/{id}/playlists", response_model=Playlist, status_code=201)
def criar_playlist(id: int, p: PlaylistIn):
    return _executar(repo.criar_playlist, p.nome, id, p.musicas)


# ---------- /musicas ----------
@app.get("/musicas", response_model=list[Musica])
def listar_musicas(pagina: int = PAG, tamanho: int = TAM):
    return repo.listar_musicas(pagina, tamanho)

@app.get("/musicas/{id}", response_model=Musica)
def obter_musica(id: int):
    return _executar(repo.obter_musica, id)

@app.post("/musicas", response_model=Musica, status_code=201)
def criar_musica(m: MusicaIn):
    return _executar(repo.criar_musica, m.nome, m.duracao_seg, m.album_id, m.genero_id)

@app.patch("/musicas/{id}", response_model=Musica)
def atualizar_musica(id: int, m: MusicaPatch):
    return _executar(repo.atualizar_musica, id, m.nome, m.duracao_seg, m.album_id, m.genero_id)

@app.delete("/musicas/{id}", status_code=204)
def remover_musica(id: int):
    _executar(repo.remover_musica, id)
    return Response(status_code=204)

@app.get("/musicas/{id}/playlists", response_model=list[Playlist])       # consulta do enunciado
def playlists_com_musica(id: int):
    return _executar(repo.playlists_com_musica, id)


# ---------- /playlists ----------
@app.get("/playlists", response_model=list[Playlist])
def listar_playlists(pagina: int = PAG, tamanho: int = TAM):
    return repo.listar_playlists(pagina, tamanho)

@app.get("/playlists/{id}", response_model=Playlist)
def obter_playlist(id: int):
    return _executar(repo.obter_playlist, id)

@app.patch("/playlists/{id}", response_model=Playlist)
def atualizar_playlist(id: int, p: PlaylistPatch):
    return _executar(repo.atualizar_playlist, id, p.nome, p.musicas)

@app.delete("/playlists/{id}", status_code=204)
def remover_playlist(id: int):
    _executar(repo.remover_playlist, id)
    return Response(status_code=204)

@app.get("/playlists/{id}/musicas", response_model=list[Musica])         # consulta do enunciado
def musicas_da_playlist(id: int):
    return _executar(repo.musicas_da_playlist, id)


# ---------- entidades extras (leitura) ----------
@app.get("/generos", response_model=list[Genero])
def listar_generos():
    return repo.listar_generos()

@app.get("/generos/{id}", response_model=Genero)
def obter_genero(id: int):
    return _executar(repo.obter_genero, id)

@app.get("/artistas", response_model=list[Artista])
def listar_artistas(pagina: int = PAG, tamanho: int = TAM):
    return repo.listar_artistas(pagina, tamanho)

@app.get("/artistas/{id}", response_model=Artista)
def obter_artista(id: int):
    return _executar(repo.obter_artista, id)

@app.get("/artistas/{id}/albuns", response_model=list[Album])
def albuns_do_artista(id: int):
    return _executar(repo.albuns_do_artista, id)

@app.get("/albuns/{id}", response_model=Album)
def obter_album(id: int):
    return _executar(repo.obter_album, id)

@app.get("/albuns/{id}/musicas", response_model=list[Musica])
def musicas_do_album(id: int):
    return _executar(repo.musicas_do_album, id)
