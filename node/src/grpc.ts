/**
 * Serviço de streaming de músicas — gRPC (Node.js + @grpc/grpc-js).
 * Usa o MESMO contrato da versão Python (contratos/streaming.proto), carregado em tempo de execução.
 *
 * Executar (na pasta node/):  node src/grpc.ts        (porta 50052; mude com PORTA=...)
 */
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import { fileURLToPath } from "node:url";
import { ErroNaoEncontrado, ErroValidacao, novoRepositorio } from "./dados.ts";
import type { Musica } from "./dados.ts";

const repo = novoRepositorio();
const definicao = protoLoader.loadSync(fileURLToPath(new URL("../../contratos/streaming.proto", import.meta.url)), {
  keepCase: true,   // mantém os nomes snake_case do .proto (duracao_seg, usuario_id...)
  defaults: false,  // campo não enviado chega como undefined (usado na atualização parcial)
  oneofs: true,
});
const proto = grpc.loadPackageDefinition(definicao) as any;

type Callback = grpc.sendUnaryData<any>;

/** Transforma uma função assíncrona num handler unário, convertendo erros em status gRPC. */
const unario = (fn: (req: any) => Promise<any>) =>
  (call: grpc.ServerUnaryCall<any, any>, cb: Callback) => {
    fn(call.request).then((r) => cb(null, r ?? {})).catch((e) => {
      if (e instanceof ErroNaoEncontrado) return cb({ code: grpc.status.NOT_FOUND, details: e.message });
      if (e instanceof ErroValidacao) return cb({ code: grpc.status.INVALID_ARGUMENT, details: e.message });
      console.error(e);
      cb({ code: grpc.status.INTERNAL, details: "Erro interno" });
    });
  };

const servico = {
  // ---------- usuários ----------
  ListarUsuarios: unario(async (q) => ({ usuarios: await repo.listarUsuarios(q.pagina, q.tamanho) })),
  ObterUsuario: unario((q) => repo.obterUsuario(q.id)),
  CriarUsuario: unario((q) => repo.criarUsuario(q.nome, q.idade)),
  AtualizarUsuario: unario((q) => repo.atualizarUsuario(q.id, q.nome, q.idade)),
  RemoverUsuario: unario((q) => repo.removerUsuario(q.id)),

  // ---------- músicas ----------
  ListarMusicas: unario(async (q) => ({ musicas: await repo.listarMusicas(q.pagina, q.tamanho) })),
  ObterMusica: unario((q) => repo.obterMusica(q.id)),
  CriarMusica: unario((q) => repo.criarMusica(q.nome, q.duracao_seg, q.album_id, q.genero_id)),
  AtualizarMusica: unario((q) => repo.atualizarMusica(q.id, q.nome, q.duracao_seg, q.album_id, q.genero_id)),
  RemoverMusica: unario((q) => repo.removerMusica(q.id)),

  // ---------- playlists ----------
  ListarPlaylists: unario(async (q) => ({ playlists: await repo.listarPlaylists(q.pagina, q.tamanho) })),
  ObterPlaylist: unario((q) => repo.obterPlaylist(q.id)),
  CriarPlaylist: unario((q) => repo.criarPlaylist(q.nome, q.usuario_id, q.musicas ?? [])),
  AtualizarPlaylist: unario((q) => repo.atualizarPlaylist(q.id, q.nome, q.trocar_musicas ? (q.musicas ?? []) : null)),
  RemoverPlaylist: unario((q) => repo.removerPlaylist(q.id)),

  // ---------- consultas do enunciado ----------
  PlaylistsDoUsuario: unario(async (q) => ({ playlists: await repo.playlistsDoUsuario(q.id) })),
  MusicasDaPlaylist: unario(async (q) => ({ musicas: await repo.musicasDaPlaylist(q.id) })),
  PlaylistsComMusica: unario(async (q) => ({ playlists: await repo.playlistsComMusica(q.id) })),

  // ---------- entidades extras ----------
  ListarGeneros: unario(async () => ({ generos: await repo.listarGeneros() })),
  ObterGenero: unario((q) => repo.obterGenero(q.id)),
  ListarArtistas: unario(async (q) => ({ artistas: await repo.listarArtistas(q.pagina, q.tamanho) })),
  ObterArtista: unario((q) => repo.obterArtista(q.id)),
  AlbunsDoArtista: unario(async (q) => ({ albuns: await repo.albunsDoArtista(q.id) })),
  ObterAlbum: unario((q) => repo.obterAlbum(q.id)),
  MusicasDoAlbum: unario(async (q) => ({ musicas: await repo.musicasDoAlbum(q.id) })),

  // ---------- server streaming ----------
  TransmitirMusicasDaPlaylist: (call: grpc.ServerWritableStream<any, Musica>) => {
    repo.musicasDaPlaylist(call.request.id)
      .then((musicas) => { for (const m of musicas) call.write(m); call.end(); })
      .catch((e) => call.destroy(Object.assign(new Error(e.message), {
        code: e instanceof ErroNaoEncontrado ? grpc.status.NOT_FOUND : grpc.status.INTERNAL,
      })));
  },
};

const server = new grpc.Server();
server.addService(proto.streaming.Streaming.service, servico);
const porta = Number(process.env.PORTA ?? 50052);
server.bindAsync(`0.0.0.0:${porta}`, grpc.ServerCredentials.createInsecure(), (err) => {
  if (err) throw err;
  console.log(`gRPC (Node.js) ouvindo na porta ${porta}`);
});
