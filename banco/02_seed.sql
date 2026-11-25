-- Dados iniciais determinísticos (mesma semente => mesmos dados em qualquer máquina).
-- Volume: 20 gêneros, 2.000 artistas, 10.000 álbuns, 100.000 músicas,
--         10.000 usuários, 30.000 playlists e 600.000 ligações playlist-música.
SELECT setseed(0.42);

INSERT INTO generos (nome)
SELECT unnest(ARRAY['MPB','Samba','Bossa Nova','Forró','Sertanejo','Axé','Funk','Rock',
                    'Pop','Rap','Reggae','Pagode','Frevo','Baião','Jazz','Blues',
                    'Eletrônica','Clássica','Gospel','Indie']);

INSERT INTO artistas (nome, pais)
SELECT 'Artista ' || g,
       (ARRAY['Brasil','Portugal','Angola','Argentina','EUA','Reino Unido'])[1 + floor(random() * 6)::int]
FROM generate_series(1, 2000) g;

INSERT INTO albuns (titulo, ano, artista_id)
SELECT 'Álbum ' || g, 1960 + floor(random() * 66)::int, 1 + (g - 1) % 2000
FROM generate_series(1, 10000) g;

INSERT INTO musicas (nome, duracao_seg, album_id, genero_id)
SELECT 'Música ' || g, 120 + floor(random() * 300)::int, 1 + (g - 1) % 10000, 1 + floor(random() * 20)::int
FROM generate_series(1, 100000) g;

INSERT INTO usuarios (nome, idade)
SELECT (ARRAY['Ana','Bruno','Carla','Diego','Elisa','Felipe','Gabriela','Hugo','Isabela','João',
              'Larissa','Mateus','Natália','Otávio','Paula','Rafael'])[1 + floor(random() * 16)::int] || ' ' || g,
       14 + floor(random() * 57)::int
FROM generate_series(1, 10000) g;

-- 3 playlists por usuário: playlist p pertence ao usuário ceil(p/3)
INSERT INTO playlists (nome, usuario_id)
SELECT 'Playlist ' || (1 + (g - 1) % 3) || ' do usuário ' || (1 + (g - 1) / 3), 1 + (g - 1) / 3
FROM generate_series(1, 30000) g;

-- 20 músicas por playlist
INSERT INTO playlist_musica (playlist_id, musica_id, posicao)
SELECT p, 1 + floor(random() * 100000)::int, pos
FROM generate_series(1, 30000) p, generate_series(1, 20) pos;

ANALYZE;
