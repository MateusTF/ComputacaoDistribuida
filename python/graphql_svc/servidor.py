"""
Serviço de streaming de músicas — GraphQL (Python + Strawberry sobre FastAPI).

Um único endpoint (/graphql). Esquema fortemente tipado; o cliente escolhe os campos e
navega pelos relacionamentos (usuário → playlists → músicas → álbum → artista).
O esquema gerado é exportado para contratos/streaming.graphql e reutilizado pela versão Node.js.

Executar (na pasta python/):  uvicorn graphql_svc.servidor:app --port 8002
"""
from __future__ import annotations

from functools import partial

import strawberry
from anyio import to_thread
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from comum import dados
from comum.dados import novo_repositorio

repo = novo_repositorio()


async def bd(fn, *args):
    """Executa a consulta (bloqueante) numa thread, sem travar o laço de eventos."""
    return await to_thread.run_sync(partial(fn, *args))


# ---------- tipos ----------
@strawberry.type
class Genero:
    id: int
    nome: str


@strawberry.type
class Artista:
    id: int
    nome: str
    pais: str

    @strawberry.field
    async def albuns(self) -> list[Album]:
        return [Album.de(a) for a in await bd(repo.albuns_do_artista, self.id)]

    @staticmethod
    def de(a: dados.Artista) -> Artista:
        return Artista(id=a.id, nome=a.nome, pais=a.pais)


@strawberry.type
class Album:
    id: int
    titulo: str
    ano: int
    artista_id: int

    @strawberry.field
    async def artista(self) -> Artista:
        return Artista.de(await bd(repo.obter_artista, self.artista_id))

    @strawberry.field
    async def musicas(self) -> list[Musica]:
        return [Musica.de(m) for m in await bd(repo.musicas_do_album, self.id)]

    @staticmethod
    def de(a: dados.Album) -> Album:
        return Album(id=a.id, titulo=a.titulo, ano=a.ano, artista_id=a.artista_id)


@strawberry.type
class Musica:
    id: int
    nome: str
    duracao_seg: int
    album_id: int
    genero_id: int

    @strawberry.field
    async def album(self) -> Album:
        return Album.de(await bd(repo.obter_album, self.album_id))

    @strawberry.field
    async def genero(self) -> Genero:
        g = await bd(repo.obter_genero, self.genero_id)
        return Genero(id=g.id, nome=g.nome)

    @strawberry.field
    async def playlists(self) -> list[Playlist]:                       # Música -> 0..* Playlists
        return [Playlist.de(p) for p in await bd(repo.playlists_com_musica, self.id)]

    @staticmethod
    def de(m: dados.Musica) -> Musica:
        return Musica(id=m.id, nome=m.nome, duracao_seg=m.duracao_seg, album_id=m.album_id, genero_id=m.genero_id)


@strawberry.type
class Playlist:
    id: int
    nome: str
    usuario_id: int

    @strawberry.field
    async def usuario(self) -> Usuario:
        return Usuario.de(await bd(repo.obter_usuario, self.usuario_id))

    @strawberry.field
    async def musicas(self) -> list[Musica]:                           # Playlist -> 1..* Músicas
        return [Musica.de(m) for m in await bd(repo.musicas_da_playlist, self.id)]

    @staticmethod
    def de(p: dados.Playlist) -> Playlist:
        return Playlist(id=p.id, nome=p.nome, usuario_id=p.usuario_id)


@strawberry.type
class Usuario:
    id: int
    nome: str
    idade: int

    @strawberry.field
    async def playlists(self) -> list[Playlist]:                       # Usuário -> 0..* Playlists
        return [Playlist.de(p) for p in await bd(repo.playlists_do_usuario, self.id)]

    @staticmethod
    def de(u: dados.Usuario) -> Usuario:
        return Usuario(id=u.id, nome=u.nome, idade=u.idade)


# ---------- consultas ----------
@strawberry.type
class Query:
    @strawberry.field
    async def usuarios(self, pagina: int = 1, tamanho: int = 100) -> list[Usuario]:
        return [Usuario.de(u) for u in await bd(repo.listar_usuarios, pagina, tamanho)]

    @strawberry.field
    async def usuario(self, id: int) -> Usuario:
        return Usuario.de(await bd(repo.obter_usuario, id))

    @strawberry.field
    async def musicas(self, pagina: int = 1, tamanho: int = 100) -> list[Musica]:
        return [Musica.de(m) for m in await bd(repo.listar_musicas, pagina, tamanho)]

    @strawberry.field
    async def musica(self, id: int) -> Musica:
        return Musica.de(await bd(repo.obter_musica, id))

    @strawberry.field
    async def playlists(self, pagina: int = 1, tamanho: int = 100) -> list[Playlist]:
        return [Playlist.de(p) for p in await bd(repo.listar_playlists, pagina, tamanho)]

    @strawberry.field
    async def playlist(self, id: int) -> Playlist:
        return Playlist.de(await bd(repo.obter_playlist, id))

    @strawberry.field
    async def generos(self) -> list[Genero]:
        return [Genero(id=g.id, nome=g.nome) for g in await bd(repo.listar_generos)]

    @strawberry.field
    async def artistas(self, pagina: int = 1, tamanho: int = 100) -> list[Artista]:
        return [Artista.de(a) for a in await bd(repo.listar_artistas, pagina, tamanho)]

    @strawberry.field
    async def artista(self, id: int) -> Artista:
        return Artista.de(await bd(repo.obter_artista, id))

    @strawberry.field
    async def album(self, id: int) -> Album:
        return Album.de(await bd(repo.obter_album, id))


# ---------- mutações ----------
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def criar_usuario(self, nome: str, idade: int) -> Usuario:
        return Usuario.de(await bd(repo.criar_usuario, nome, idade))

    @strawberry.mutation
    async def atualizar_usuario(self, id: int, nome: str | None = None, idade: int | None = None) -> Usuario:
        return Usuario.de(await bd(repo.atualizar_usuario, id, nome, idade))

    @strawberry.mutation
    async def remover_usuario(self, id: int) -> bool:
        await bd(repo.remover_usuario, id)
        return True

    @strawberry.mutation
    async def criar_musica(self, nome: str, duracao_seg: int, album_id: int, genero_id: int) -> Musica:
        return Musica.de(await bd(repo.criar_musica, nome, duracao_seg, album_id, genero_id))

    @strawberry.mutation
    async def atualizar_musica(self, id: int, nome: str | None = None, duracao_seg: int | None = None,
                               album_id: int | None = None, genero_id: int | None = None) -> Musica:
        return Musica.de(await bd(repo.atualizar_musica, id, nome, duracao_seg, album_id, genero_id))

    @strawberry.mutation
    async def remover_musica(self, id: int) -> bool:
        await bd(repo.remover_musica, id)
        return True

    @strawberry.mutation
    async def criar_playlist(self, nome: str, usuario_id: int, musicas: list[int]) -> Playlist:
        return Playlist.de(await bd(repo.criar_playlist, nome, usuario_id, musicas))

    @strawberry.mutation
    async def atualizar_playlist(self, id: int, nome: str | None = None,
                                 musicas: list[int] | None = None) -> Playlist:
        return Playlist.de(await bd(repo.atualizar_playlist, id, nome, musicas))

    @strawberry.mutation
    async def remover_playlist(self, id: int) -> bool:
        await bd(repo.remover_playlist, id)
        return True


schema = strawberry.Schema(query=Query, mutation=Mutation)
app = FastAPI(title="Streaming de Músicas — GraphQL (Python)")
app.include_router(GraphQLRouter(schema), prefix="/graphql")

if __name__ == "__main__":   # python -m graphql_svc.servidor  -> exporta o esquema (SDL)
    print(schema.as_str())
