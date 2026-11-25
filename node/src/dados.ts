/**
 * Camada de dados (PostgreSQL) compartilhada pelos 4 serviços Node.js.
 * Executa exatamente as mesmas consultas SQL da versão Python (python/comum/dados.py).
 *
 * Conexão: variável de ambiente DATABASE_URL (padrão: postgresql://streaming@localhost:5432/streaming)
 */
import pg from "pg";

export const TAMANHO_PADRAO = 100;
export const TAMANHO_MAXIMO = 1000;

// ------------------------------------------------------------------ modelos
export interface Usuario { id: number; nome: string; idade: number }
export interface Genero { id: number; nome: string }
export interface Artista { id: number; nome: string; pais: string }
export interface Album { id: number; titulo: string; ano: number; artista_id: number }
export interface Musica { id: number; nome: string; duracao_seg: number; album_id: number; genero_id: number }
export interface Playlist { id: number; nome: string; usuario_id: number; musicas: number[] }

export class ErroNaoEncontrado extends Error {}
export class ErroValidacao extends Error {}

// ------------------------------------------------------------------ SQL
const SQL_PLAYLIST = `
    SELECT p.id, p.nome, p.usuario_id,
           COALESCE(array_agg(pm.musica_id ORDER BY pm.posicao)
                    FILTER (WHERE pm.musica_id IS NOT NULL), '{}') AS musicas
    FROM playlists p
    LEFT JOIN playlist_musica pm ON pm.playlist_id = p.id`;
const COLS_MUSICA = "id, nome, duracao_seg, album_id, genero_id";
const FK_VIOLATION = "23503";

function paginacao(pagina?: number | null, tamanho?: number | null): [number, number] {
  const p = Math.max(1, pagina || 1);
  const t = Math.min(TAMANHO_MAXIMO, Math.max(1, tamanho || TAMANHO_PADRAO));
  return [t, (p - 1) * t];
}

export class Repositorio {
  pool: pg.Pool;

  constructor(url?: string, tamanhoPool?: number) {
    this.pool = new pg.Pool({
      connectionString: url ?? process.env.DATABASE_URL ?? "postgresql://streaming@localhost:5432/streaming",
      max: tamanhoPool ?? Number(process.env.POOL_SIZE ?? 10),
    });
    // falha logo ao iniciar se o banco não estiver acessível (em vez de errar só na 1ª requisição)
    this.pool.query("SELECT 1").catch((e) => {
      console.error(`ERRO: não consegui conectar ao banco (${e.message}). O PostgreSQL está no ar? ` +
                    "(com Docker: docker compose up -d db)");
      process.exit(1);
    });
  }

  // ---------- utilitários ----------
  async lista<T>(sql: string, params: unknown[] = []): Promise<T[]> {
    return (await this.pool.query(sql, params)).rows as T[];
  }

  async um<T>(sql: string, params: unknown[], nome: string): Promise<T> {
    const r = await this.pool.query(sql, params);
    if (r.rowCount === 0) throw new ErroNaoEncontrado(`${nome} ${params[0]} não encontrado(a)`);
    return r.rows[0] as T;
  }

  async existe(tabela: string, id: number, nome: string): Promise<void> {
    const r = await this.pool.query(`SELECT 1 FROM ${tabela} WHERE id = $1`, [id]);
    if (r.rowCount === 0) throw new ErroNaoEncontrado(`${nome} ${id} não encontrado(a)`);
  }

  async remover(tabela: string, id: number, nome: string): Promise<void> {
    const r = await this.pool.query(`DELETE FROM ${tabela} WHERE id = $1`, [id]);
    if (r.rowCount === 0) throw new ErroNaoEncontrado(`${nome} ${id} não encontrado(a)`);
  }

  // ---------- usuários ----------
  listarUsuarios(pagina?: number, tamanho?: number) {
    return this.lista<Usuario>("SELECT id, nome, idade FROM usuarios ORDER BY id LIMIT $1 OFFSET $2", paginacao(pagina, tamanho));
  }
  obterUsuario(id: number) {
    return this.um<Usuario>("SELECT id, nome, idade FROM usuarios WHERE id = $1", [id], "Usuário");
  }
  criarUsuario(nome: string, idade: number) {
    return this.um<Usuario>("INSERT INTO usuarios (nome, idade) VALUES ($1, $2) RETURNING id, nome, idade", [nome, idade], "Usuário");
  }
  atualizarUsuario(id: number, nome?: string | null, idade?: number | null) {
    return this.um<Usuario>(`UPDATE usuarios SET nome = COALESCE($2, nome), idade = COALESCE($3, idade)
                             WHERE id = $1 RETURNING id, nome, idade`, [id, nome ?? null, idade ?? null], "Usuário");
  }
  removerUsuario(id: number) {
    return this.remover("usuarios", id, "Usuário"); // ON DELETE CASCADE remove as playlists
  }

  // ---------- músicas ----------
  listarMusicas(pagina?: number, tamanho?: number) {
    return this.lista<Musica>(`SELECT ${COLS_MUSICA} FROM musicas ORDER BY id LIMIT $1 OFFSET $2`, paginacao(pagina, tamanho));
  }
  obterMusica(id: number) {
    return this.um<Musica>(`SELECT ${COLS_MUSICA} FROM musicas WHERE id = $1`, [id], "Música");
  }
  async criarMusica(nome: string, duracao_seg: number, album_id: number, genero_id: number) {
    try {
      return await this.um<Musica>(`INSERT INTO musicas (nome, duracao_seg, album_id, genero_id) VALUES ($1, $2, $3, $4)
                                    RETURNING ${COLS_MUSICA}`, [nome, duracao_seg, album_id, genero_id], "Música");
    } catch (e: any) {
      if (e.code === FK_VIOLATION) throw new ErroValidacao("Álbum ou gênero inexistente");
      throw e;
    }
  }
  async atualizarMusica(id: number, nome?: string | null, duracao_seg?: number | null,
                        album_id?: number | null, genero_id?: number | null) {
    try {
      return await this.um<Musica>(`UPDATE musicas SET nome = COALESCE($2, nome), duracao_seg = COALESCE($3, duracao_seg),
              album_id = COALESCE($4, album_id), genero_id = COALESCE($5, genero_id) WHERE id = $1 RETURNING ${COLS_MUSICA}`,
        [id, nome ?? null, duracao_seg ?? null, album_id ?? null, genero_id ?? null], "Música");
    } catch (e: any) {
      if (e.code === FK_VIOLATION) throw new ErroValidacao("Álbum ou gênero inexistente");
      throw e;
    }
  }
  removerMusica(id: number) {
    return this.remover("musicas", id, "Música");
  }

  // ---------- playlists ----------
  listarPlaylists(pagina?: number, tamanho?: number) {
    return this.lista<Playlist>(SQL_PLAYLIST + ` WHERE p.id IN (SELECT id FROM playlists ORDER BY id LIMIT $1 OFFSET $2)
                                                GROUP BY p.id ORDER BY p.id`, paginacao(pagina, tamanho));
  }
  obterPlaylist(id: number) {
    return this.um<Playlist>(SQL_PLAYLIST + " WHERE p.id = $1 GROUP BY p.id", [id], "Playlist");
  }

  /** Executa fn dentro de uma transação, numa conexão exclusiva do pool. */
  async transacao<T>(fn: (c: pg.PoolClient) => Promise<T>): Promise<T> {
    const c = await this.pool.connect();
    try {
      await c.query("BEGIN");
      const r = await fn(c);
      await c.query("COMMIT");
      return r;
    } catch (e) {
      await c.query("ROLLBACK");
      throw e;
    } finally {
      c.release();
    }
  }

  async gravarMusicas(c: pg.PoolClient, playlistId: number, musicas: number[]) {
    if (!musicas || musicas.length === 0) throw new ErroValidacao("Uma playlist deve conter pelo menos uma música (1..*)");
    await c.query("DELETE FROM playlist_musica WHERE playlist_id = $1", [playlistId]);
    await c.query(`INSERT INTO playlist_musica (playlist_id, musica_id, posicao)
                   SELECT $1, m, pos FROM unnest($2::int[]) WITH ORDINALITY AS t(m, pos)`, [playlistId, musicas]);
  }

  async criarPlaylist(nome: string, usuario_id: number, musicas: number[]) {
    let pid: number;
    try {
      pid = await this.transacao(async (c) => {
        const r = await c.query("INSERT INTO playlists (nome, usuario_id) VALUES ($1, $2) RETURNING id", [nome, usuario_id]);
        await this.gravarMusicas(c, r.rows[0].id, musicas);
        return r.rows[0].id as number;
      });
    } catch (e: any) {
      if (e.code === FK_VIOLATION) throw new ErroNaoEncontrado("Usuário ou música inexistente");
      throw e;
    }
    return this.obterPlaylist(pid);
  }

  async atualizarPlaylist(id: number, nome?: string | null, musicas?: number[] | null) {
    try {
      await this.transacao(async (c) => {
        const r = await c.query("UPDATE playlists SET nome = COALESCE($2, nome) WHERE id = $1", [id, nome ?? null]);
        if (r.rowCount === 0) throw new ErroNaoEncontrado(`Playlist ${id} não encontrado(a)`);
        if (musicas != null) await this.gravarMusicas(c, id, musicas);
      });
    } catch (e: any) {
      if (e.code === FK_VIOLATION) throw new ErroNaoEncontrado("Música inexistente");
      throw e;
    }
    return this.obterPlaylist(id);
  }

  removerPlaylist(id: number) {
    return this.remover("playlists", id, "Playlist");
  }

  // ---------- consultas do enunciado ----------
  async playlistsDoUsuario(usuarioId: number) {
    const r = await this.lista<Playlist>(SQL_PLAYLIST + " WHERE p.usuario_id = $1 GROUP BY p.id ORDER BY p.id", [usuarioId]);
    if (r.length === 0) await this.existe("usuarios", usuarioId, "Usuário");
    return r;
  }
  async musicasDaPlaylist(playlistId: number) {
    const r = await this.lista<Musica>(`SELECT m.id, m.nome, m.duracao_seg, m.album_id, m.genero_id
                                        FROM playlist_musica pm JOIN musicas m ON m.id = pm.musica_id
                                        WHERE pm.playlist_id = $1 ORDER BY pm.posicao`, [playlistId]);
    if (r.length === 0) await this.existe("playlists", playlistId, "Playlist");
    return r;
  }
  async playlistsComMusica(musicaId: number) {
    const r = await this.lista<Playlist>(SQL_PLAYLIST + ` WHERE p.id IN (SELECT playlist_id FROM playlist_musica
                                                          WHERE musica_id = $1) GROUP BY p.id ORDER BY p.id`, [musicaId]);
    if (r.length === 0) await this.existe("musicas", musicaId, "Música");
    return r;
  }

  // ---------- entidades extras (leitura) ----------
  listarGeneros() {
    return this.lista<Genero>("SELECT id, nome FROM generos ORDER BY id");
  }
  obterGenero(id: number) {
    return this.um<Genero>("SELECT id, nome FROM generos WHERE id = $1", [id], "Gênero");
  }
  listarArtistas(pagina?: number, tamanho?: number) {
    return this.lista<Artista>("SELECT id, nome, pais FROM artistas ORDER BY id LIMIT $1 OFFSET $2", paginacao(pagina, tamanho));
  }
  obterArtista(id: number) {
    return this.um<Artista>("SELECT id, nome, pais FROM artistas WHERE id = $1", [id], "Artista");
  }
  async albunsDoArtista(artistaId: number) {
    const r = await this.lista<Album>("SELECT id, titulo, ano, artista_id FROM albuns WHERE artista_id = $1 ORDER BY id", [artistaId]);
    if (r.length === 0) await this.existe("artistas", artistaId, "Artista");
    return r;
  }
  obterAlbum(id: number) {
    return this.um<Album>("SELECT id, titulo, ano, artista_id FROM albuns WHERE id = $1", [id], "Álbum");
  }
  async musicasDoAlbum(albumId: number) {
    const r = await this.lista<Musica>(`SELECT ${COLS_MUSICA} FROM musicas WHERE album_id = $1 ORDER BY id`, [albumId]);
    if (r.length === 0) await this.existe("albuns", albumId, "Álbum");
    return r;
  }
}

export const novoRepositorio = () => new Repositorio();
