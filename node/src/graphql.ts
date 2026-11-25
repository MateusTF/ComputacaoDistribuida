/**
 * Serviço de streaming de músicas — GraphQL (Node.js + GraphQL Yoga).
 * O esquema (SDL) é o MESMO da versão Python: contratos/streaming.graphql.
 * Interface GraphiQL em http://localhost:9002/graphql
 *
 * Executar (na pasta node/):  node src/graphql.ts        (porta 9002; mude com PORTA=...)
 */
import { readFileSync } from "node:fs";
import { createServer } from "node:http";
import { GraphQLError } from "graphql";
import { createSchema, createYoga } from "graphql-yoga";
import { ErroNaoEncontrado, ErroValidacao, novoRepositorio } from "./dados.ts";
import type { Album, Artista, Musica, Playlist, Usuario } from "./dados.ts";

const repo = novoRepositorio();
const typeDefs = readFileSync(new URL("../../contratos/streaming.graphql", import.meta.url), "utf8");

/** Erros do domínio viram erros GraphQL com a mensagem original (o Yoga oculta os demais). */
const r = <T>(p: Promise<T>): Promise<T> =>
  p.catch((e) => {
    if (e instanceof ErroNaoEncontrado || e instanceof ErroValidacao) throw new GraphQLError(e.message);
    throw e;
  });

const resolvers = {
  Query: {
    usuarios: (_: unknown, a: any) => r(repo.listarUsuarios(a.pagina, a.tamanho)),
    usuario: (_: unknown, a: any) => r(repo.obterUsuario(a.id)),
    musicas: (_: unknown, a: any) => r(repo.listarMusicas(a.pagina, a.tamanho)),
    musica: (_: unknown, a: any) => r(repo.obterMusica(a.id)),
    playlists: (_: unknown, a: any) => r(repo.listarPlaylists(a.pagina, a.tamanho)),
    playlist: (_: unknown, a: any) => r(repo.obterPlaylist(a.id)),
    generos: () => r(repo.listarGeneros()),
    artistas: (_: unknown, a: any) => r(repo.listarArtistas(a.pagina, a.tamanho)),
    artista: (_: unknown, a: any) => r(repo.obterArtista(a.id)),
    album: (_: unknown, a: any) => r(repo.obterAlbum(a.id)),
  },
  Mutation: {
    criarUsuario: (_: unknown, a: any) => r(repo.criarUsuario(a.nome, a.idade)),
    atualizarUsuario: (_: unknown, a: any) => r(repo.atualizarUsuario(a.id, a.nome, a.idade)),
    removerUsuario: async (_: unknown, a: any) => { await r(repo.removerUsuario(a.id)); return true; },
    criarMusica: (_: unknown, a: any) => r(repo.criarMusica(a.nome, a.duracaoSeg, a.albumId, a.generoId)),
    atualizarMusica: (_: unknown, a: any) => r(repo.atualizarMusica(a.id, a.nome, a.duracaoSeg, a.albumId, a.generoId)),
    removerMusica: async (_: unknown, a: any) => { await r(repo.removerMusica(a.id)); return true; },
    criarPlaylist: (_: unknown, a: any) => r(repo.criarPlaylist(a.nome, a.usuarioId, a.musicas)),
    atualizarPlaylist: (_: unknown, a: any) => r(repo.atualizarPlaylist(a.id, a.nome, a.musicas)),
    removerPlaylist: async (_: unknown, a: any) => { await r(repo.removerPlaylist(a.id)); return true; },
  },
  // Relacionamentos: cada campo é resolvido sob demanda (só se o cliente pedir)
  Usuario: {
    playlists: (u: Usuario) => r(repo.playlistsDoUsuario(u.id)),               // Usuário -> 0..* Playlists
  },
  Playlist: {
    usuarioId: (p: Playlist) => p.usuario_id,
    usuario: (p: Playlist) => r(repo.obterUsuario(p.usuario_id)),
    musicas: (p: Playlist) => r(repo.musicasDaPlaylist(p.id)),                 // Playlist -> 1..* Músicas
  },
  Musica: {
    duracaoSeg: (m: Musica) => m.duracao_seg,
    albumId: (m: Musica) => m.album_id,
    generoId: (m: Musica) => m.genero_id,
    album: (m: Musica) => r(repo.obterAlbum(m.album_id)),
    genero: (m: Musica) => r(repo.obterGenero(m.genero_id)),
    playlists: (m: Musica) => r(repo.playlistsComMusica(m.id)),                // Música -> 0..* Playlists
  },
  Album: {
    artistaId: (a: Album) => a.artista_id,
    artista: (a: Album) => r(repo.obterArtista(a.artista_id)),
    musicas: (a: Album) => r(repo.musicasDoAlbum(a.id)),
  },
  Artista: {
    albuns: (a: Artista) => r(repo.albunsDoArtista(a.id)),
  },
};

const yoga = createYoga({ schema: createSchema({ typeDefs, resolvers }), logging: "warn" });
const porta = Number(process.env.PORTA ?? 9002);
createServer(yoga).listen(porta, () => console.log(`GraphQL (Node.js) ouvindo na porta ${porta}`));
