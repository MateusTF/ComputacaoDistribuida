"""
Camada de dados (PostgreSQL) compartilhada pelos 4 serviços Python.
A versão Node.js (node/src/dados.ts) executa exatamente as mesmas consultas SQL.

Entidades:  Usuario, Musica, Playlist (enunciado) + Artista, Album, Genero (extras)
Conexão:    variável de ambiente DATABASE_URL (padrão: postgresql://streaming@localhost:5432/streaming)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from psycopg.errors import ForeignKeyViolation
from psycopg.rows import class_row
from psycopg_pool import ConnectionPool, PoolTimeout

TAMANHO_PADRAO = 100
TAMANHO_MAXIMO = 1000


# ------------------------------------------------------------------ modelos
@dataclass
class Usuario:
    id: int
    nome: str
    idade: int


@dataclass
class Genero:
    id: int
    nome: str


@dataclass
class Artista:
    id: int
    nome: str
    pais: str


@dataclass
class Album:
    id: int
    titulo: str
    ano: int
    artista_id: int


@dataclass
class Musica:
    id: int
    nome: str
    duracao_seg: int
    album_id: int
    genero_id: int


@dataclass
class Playlist:
    id: int
    nome: str
    usuario_id: int
    musicas: list[int] = field(default_factory=list)


class ErroNaoEncontrado(Exception):
    pass


class ErroValidacao(Exception):
    pass


# ------------------------------------------------------------------ SQL
SQL_PLAYLIST = """
    SELECT p.id, p.nome, p.usuario_id,
           COALESCE(array_agg(pm.musica_id ORDER BY pm.posicao)
                    FILTER (WHERE pm.musica_id IS NOT NULL), '{}') AS musicas
    FROM playlists p
    LEFT JOIN playlist_musica pm ON pm.playlist_id = p.id
"""


def _paginacao(pagina: int | None, tamanho: int | None) -> tuple[int, int]:
    pagina = max(1, pagina or 1)
    tamanho = min(TAMANHO_MAXIMO, max(1, tamanho or TAMANHO_PADRAO))
    return tamanho, (pagina - 1) * tamanho


class Repositorio:
    def __init__(self, url: str | None = None, tamanho_pool: int | None = None):
        url = url or os.environ.get("DATABASE_URL", "postgresql://streaming@localhost:5432/streaming")
        n = tamanho_pool or int(os.environ.get("POOL_SIZE", "10"))
        self.pool = ConnectionPool(url, min_size=n, max_size=n, open=True)
        try:
            self.pool.wait(timeout=15)
        except PoolTimeout:
            self.pool.close()
            raise SystemExit(f"ERRO: não consegui conectar ao banco em {url}. "
                             "O PostgreSQL está no ar? (com Docker: docker compose up -d db)")

    # ---------- utilitários ----------
    def _lista(self, cls, sql, params=()):
        with self.pool.connection() as c, c.cursor(row_factory=class_row(cls)) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _um(self, cls, sql, params, nome):
        with self.pool.connection() as c, c.cursor(row_factory=class_row(cls)) as cur:
            cur.execute(sql, params)
            r = cur.fetchone()
        if r is None:
            raise ErroNaoEncontrado(f"{nome} {params[0]} não encontrado(a)")
        return r

    def _existe(self, tabela, id, nome):
        with self.pool.connection() as c:
            if c.execute(f"SELECT 1 FROM {tabela} WHERE id = %s", (id,)).fetchone() is None:
                raise ErroNaoEncontrado(f"{nome} {id} não encontrado(a)")

    def _remover(self, tabela, id, nome):
        with self.pool.connection() as c:
            if c.execute(f"DELETE FROM {tabela} WHERE id = %s", (id,)).rowcount == 0:
                raise ErroNaoEncontrado(f"{nome} {id} não encontrado(a)")

    # ---------- usuários ----------
    def listar_usuarios(self, pagina=None, tamanho=None):
        lim, off = _paginacao(pagina, tamanho)
        return self._lista(Usuario, "SELECT id, nome, idade FROM usuarios ORDER BY id LIMIT %s OFFSET %s", (lim, off))

    def obter_usuario(self, id):
        return self._um(Usuario, "SELECT id, nome, idade FROM usuarios WHERE id = %s", (id,), "Usuário")

    def criar_usuario(self, nome, idade):
        return self._um(Usuario, "INSERT INTO usuarios (nome, idade) VALUES (%s, %s) RETURNING id, nome, idade",
                        (nome, idade), "Usuário")

    def atualizar_usuario(self, id, nome=None, idade=None):
        return self._um(Usuario, """UPDATE usuarios SET nome = COALESCE(%s, nome), idade = COALESCE(%s, idade)
                                    WHERE id = %s RETURNING id, nome, idade""", (nome, idade, id), "Usuário")

    def remover_usuario(self, id):
        self._remover("usuarios", id, "Usuário")   # ON DELETE CASCADE remove as playlists

    # ---------- músicas ----------
    COLS_MUSICA = "id, nome, duracao_seg, album_id, genero_id"

    def listar_musicas(self, pagina=None, tamanho=None):
        lim, off = _paginacao(pagina, tamanho)
        return self._lista(Musica, f"SELECT {self.COLS_MUSICA} FROM musicas ORDER BY id LIMIT %s OFFSET %s", (lim, off))

    def obter_musica(self, id):
        return self._um(Musica, f"SELECT {self.COLS_MUSICA} FROM musicas WHERE id = %s", (id,), "Música")

    def criar_musica(self, nome, duracao_seg, album_id, genero_id):
        try:
            with self.pool.connection() as c, c.cursor(row_factory=class_row(Musica)) as cur:
                cur.execute(f"""INSERT INTO musicas (nome, duracao_seg, album_id, genero_id) VALUES (%s, %s, %s, %s)
                                RETURNING {self.COLS_MUSICA}""", (nome, duracao_seg, album_id, genero_id))
                return cur.fetchone()
        except ForeignKeyViolation:
            raise ErroValidacao("Álbum ou gênero inexistente")

    def atualizar_musica(self, id, nome=None, duracao_seg=None, album_id=None, genero_id=None):
        try:
            return self._um(Musica, f"""UPDATE musicas SET nome = COALESCE(%s, nome),
                    duracao_seg = COALESCE(%s, duracao_seg), album_id = COALESCE(%s, album_id),
                    genero_id = COALESCE(%s, genero_id) WHERE id = %s RETURNING {self.COLS_MUSICA}""",
                            (nome, duracao_seg, album_id, genero_id, id), "Música")
        except ForeignKeyViolation:
            raise ErroValidacao("Álbum ou gênero inexistente")

    def remover_musica(self, id):
        self._remover("musicas", id, "Música")

    # ---------- playlists ----------
    def listar_playlists(self, pagina=None, tamanho=None):
        lim, off = _paginacao(pagina, tamanho)
        return self._lista(Playlist, SQL_PLAYLIST + " WHERE p.id IN (SELECT id FROM playlists ORDER BY id LIMIT %s OFFSET %s)"
                                                    " GROUP BY p.id ORDER BY p.id", (lim, off))

    def obter_playlist(self, id):
        return self._um(Playlist, SQL_PLAYLIST + " WHERE p.id = %s GROUP BY p.id", (id,), "Playlist")

    def _gravar_musicas(self, c, playlist_id, musicas):
        if not musicas:
            raise ErroValidacao("Uma playlist deve conter pelo menos uma música (1..*)")
        c.execute("DELETE FROM playlist_musica WHERE playlist_id = %s", (playlist_id,))
        with c.cursor() as cur:
            cur.executemany("INSERT INTO playlist_musica (playlist_id, musica_id, posicao) VALUES (%s, %s, %s)",
                            [(playlist_id, m, i + 1) for i, m in enumerate(musicas)])

    def criar_playlist(self, nome, usuario_id, musicas):
        try:
            with self.pool.connection() as c:          # transação única
                pid = c.execute("INSERT INTO playlists (nome, usuario_id) VALUES (%s, %s) RETURNING id",
                                (nome, usuario_id)).fetchone()[0]
                self._gravar_musicas(c, pid, musicas)
        except ForeignKeyViolation:
            raise ErroNaoEncontrado("Usuário ou música inexistente")
        return self.obter_playlist(pid)

    def atualizar_playlist(self, id, nome=None, musicas=None):
        try:
            with self.pool.connection() as c:
                if c.execute("UPDATE playlists SET nome = COALESCE(%s, nome) WHERE id = %s",
                             (nome, id)).rowcount == 0:
                    raise ErroNaoEncontrado(f"Playlist {id} não encontrado(a)")
                if musicas is not None:
                    self._gravar_musicas(c, id, musicas)
        except ForeignKeyViolation:
            raise ErroNaoEncontrado("Música inexistente")
        return self.obter_playlist(id)

    def remover_playlist(self, id):
        self._remover("playlists", id, "Playlist")

    # ---------- consultas do enunciado ----------
    def playlists_do_usuario(self, usuario_id):
        r = self._lista(Playlist, SQL_PLAYLIST + " WHERE p.usuario_id = %s GROUP BY p.id ORDER BY p.id", (usuario_id,))
        if not r:
            self._existe("usuarios", usuario_id, "Usuário")
        return r

    def musicas_da_playlist(self, playlist_id):
        r = self._lista(Musica, """SELECT m.id, m.nome, m.duracao_seg, m.album_id, m.genero_id
                                   FROM playlist_musica pm JOIN musicas m ON m.id = pm.musica_id
                                   WHERE pm.playlist_id = %s ORDER BY pm.posicao""", (playlist_id,))
        if not r:
            self._existe("playlists", playlist_id, "Playlist")
        return r

    def playlists_com_musica(self, musica_id):
        r = self._lista(Playlist, SQL_PLAYLIST + """ WHERE p.id IN (SELECT playlist_id FROM playlist_musica
                                                   WHERE musica_id = %s) GROUP BY p.id ORDER BY p.id""", (musica_id,))
        if not r:
            self._existe("musicas", musica_id, "Música")
        return r

    # ---------- entidades extras (leitura) ----------
    def listar_generos(self):
        return self._lista(Genero, "SELECT id, nome FROM generos ORDER BY id")

    def obter_genero(self, id):
        return self._um(Genero, "SELECT id, nome FROM generos WHERE id = %s", (id,), "Gênero")

    def listar_artistas(self, pagina=None, tamanho=None):
        lim, off = _paginacao(pagina, tamanho)
        return self._lista(Artista, "SELECT id, nome, pais FROM artistas ORDER BY id LIMIT %s OFFSET %s", (lim, off))

    def obter_artista(self, id):
        return self._um(Artista, "SELECT id, nome, pais FROM artistas WHERE id = %s", (id,), "Artista")

    def albuns_do_artista(self, artista_id):
        r = self._lista(Album, "SELECT id, titulo, ano, artista_id FROM albuns WHERE artista_id = %s ORDER BY id",
                        (artista_id,))
        if not r:
            self._existe("artistas", artista_id, "Artista")
        return r

    def obter_album(self, id):
        return self._um(Album, "SELECT id, titulo, ano, artista_id FROM albuns WHERE id = %s", (id,), "Álbum")

    def musicas_do_album(self, album_id):
        r = self._lista(Musica, f"SELECT {self.COLS_MUSICA} FROM musicas WHERE album_id = %s ORDER BY id", (album_id,))
        if not r:
            self._existe("albuns", album_id, "Álbum")
        return r


def novo_repositorio() -> Repositorio:
    return Repositorio()
