-- Serviço de streaming de músicas: esquema PostgreSQL compartilhado pelas
-- 8 implementações (Python e Node.js × SOAP, REST, GraphQL e gRPC).
--
-- Entidades do enunciado: usuarios, musicas, playlists (+ playlist_musica, N:N)
-- Entidades extras:       generos, artistas, albuns
--
--   Artista 1 ── 0..* Álbum 1 ── 1..* Música *── 1 Gênero
--   Usuário 1 ── 0..* Playlist *── playlist_musica ──* Música

CREATE TABLE generos (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL UNIQUE
);

CREATE TABLE artistas (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL,
    pais  TEXT NOT NULL
);

CREATE TABLE albuns (
    id          SERIAL PRIMARY KEY,
    titulo      TEXT NOT NULL,
    ano         INT  NOT NULL,
    artista_id  INT  NOT NULL REFERENCES artistas(id) ON DELETE CASCADE
);

CREATE TABLE musicas (
    id           SERIAL PRIMARY KEY,
    nome         TEXT NOT NULL,
    duracao_seg  INT  NOT NULL,
    album_id     INT  NOT NULL REFERENCES albuns(id) ON DELETE CASCADE,
    genero_id    INT  NOT NULL REFERENCES generos(id)
);

CREATE TABLE usuarios (
    id     SERIAL PRIMARY KEY,
    nome   TEXT NOT NULL,
    idade  INT  NOT NULL
);

CREATE TABLE playlists (
    id          SERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    usuario_id  INT  NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE playlist_musica (
    playlist_id  INT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    musica_id    INT NOT NULL REFERENCES musicas(id)   ON DELETE CASCADE,
    posicao      INT NOT NULL,
    PRIMARY KEY (playlist_id, posicao)
);

-- índices para as consultas do enunciado e para os relacionamentos
CREATE INDEX ON albuns (artista_id);
CREATE INDEX ON musicas (album_id);
CREATE INDEX ON musicas (genero_id);
CREATE INDEX ON playlists (usuario_id);
CREATE INDEX ON playlist_musica (musica_id);
