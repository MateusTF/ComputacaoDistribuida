/**
 * Serviço de streaming de músicas — SOAP 1.1 (Node.js + node-soap).
 * Usa o MESMO contrato da versão Python: contratos/streaming.wsdl (gerado pelo Spyne).
 * WSDL ao vivo: http://localhost:9003/?wsdl
 *
 * Executar (na pasta node/):  node src/soap.ts        (porta 9003; mude com PORTA=...)
 */
import { readFileSync } from "node:fs";
import { createServer } from "node:http";
import * as soap from "soap";
import { ErroNaoEncontrado, ErroValidacao, novoRepositorio } from "./dados.ts";
import type { Playlist } from "./dados.ts";

const repo = novoRepositorio();
const porta = Number(process.env.PORTA ?? 9003);
// o WSDL aponta para a porta do Python; ajustamos o endereço do serviço para esta porta
const wsdl = readFileSync(new URL("../../contratos/streaming.wsdl", import.meta.url), "utf8")
  .replace(/location="[^"]*"/, `location="http://localhost:${porta}/"`);

// ---------- conversões XML <-> objetos ----------
const num = (v: unknown) => (v === undefined || v === null || v === "" ? undefined : Number(v));
/** Um array no WSDL do Spyne chega como { integer: [..] } (ou um único valor). */
const ids = (v: any): number[] => {
  const x = v?.integer;
  return x === undefined ? [] : (Array.isArray(x) ? x : [x]).map(Number);
};
const playlist = (p: Playlist) => ({ ...p, musicas: { integer: p.musicas } });

/** Converte erros do domínio em SOAP Faults (HTTP 500, como manda o SOAP 1.1). */
const fault = (e: unknown) => {
  if (e instanceof ErroNaoEncontrado || e instanceof ErroValidacao) {
    const codigo = e instanceof ErroNaoEncontrado ? "Client.ResourceNotFound" : "Client.ValidationError";
    throw { Fault: { faultcode: `soap11env:${codigo}`, faultstring: e.message, statusCode: 500 } };
  }
  throw e;
};

/** Cria a operação: chama o repositório e embrulha a resposta como o WSDL espera ({ <Op>Result: ... }). */
function op(nome: string, fn: (a: any) => Promise<unknown>, embrulho?: (r: any) => unknown) {
  return {
    [nome]: async (args: any) => {
      try {
        const r = await fn(args ?? {});
        return r === undefined ? {} : { [`${nome}Result`]: embrulho ? embrulho(r) : r };
      } catch (e) {
        return fault(e);
      }
    },
  };
}
const lista = (tipo: string, conv: (x: any) => unknown = (x) => x) => (r: any[]) => ({ [tipo]: r.map(conv) });

const operacoes = {
  // ---------- usuários ----------
  ...op("ListarUsuarios", (a) => repo.listarUsuarios(num(a.pagina), num(a.tamanho)), lista("Usuario")),
  ...op("ObterUsuario", (a) => repo.obterUsuario(Number(a.id))),
  ...op("CriarUsuario", (a) => repo.criarUsuario(a.nome, Number(a.idade))),
  ...op("AtualizarUsuario", (a) => repo.atualizarUsuario(Number(a.id), a.nome, num(a.idade))),
  ...op("RemoverUsuario", async (a) => { await repo.removerUsuario(Number(a.id)); }),

  // ---------- músicas ----------
  ...op("ListarMusicas", (a) => repo.listarMusicas(num(a.pagina), num(a.tamanho)), lista("Musica")),
  ...op("ObterMusica", (a) => repo.obterMusica(Number(a.id))),
  ...op("CriarMusica", (a) => repo.criarMusica(a.nome, Number(a.duracao_seg), Number(a.album_id), Number(a.genero_id))),
  ...op("AtualizarMusica", (a) => repo.atualizarMusica(Number(a.id), a.nome, num(a.duracao_seg), num(a.album_id), num(a.genero_id))),
  ...op("RemoverMusica", async (a) => { await repo.removerMusica(Number(a.id)); }),

  // ---------- playlists ----------
  ...op("ListarPlaylists", (a) => repo.listarPlaylists(num(a.pagina), num(a.tamanho)), lista("Playlist", playlist)),
  ...op("ObterPlaylist", (a) => repo.obterPlaylist(Number(a.id)), playlist),
  ...op("CriarPlaylist", (a) => repo.criarPlaylist(a.nome, Number(a.usuario_id), ids(a.musicas)), playlist),
  ...op("AtualizarPlaylist", (a) => repo.atualizarPlaylist(Number(a.id), a.nome, a.musicas ? ids(a.musicas) : null), playlist),
  ...op("RemoverPlaylist", async (a) => { await repo.removerPlaylist(Number(a.id)); }),

  // ---------- consultas do enunciado ----------
  ...op("PlaylistsDoUsuario", (a) => repo.playlistsDoUsuario(Number(a.id)), lista("Playlist", playlist)),
  ...op("MusicasDaPlaylist", (a) => repo.musicasDaPlaylist(Number(a.id)), lista("Musica")),
  ...op("PlaylistsComMusica", (a) => repo.playlistsComMusica(Number(a.id)), lista("Playlist", playlist)),

  // ---------- entidades extras ----------
  ...op("ListarGeneros", () => repo.listarGeneros(), lista("Genero")),
  ...op("ObterGenero", (a) => repo.obterGenero(Number(a.id))),
  ...op("ListarArtistas", (a) => repo.listarArtistas(num(a.pagina), num(a.tamanho)), lista("Artista")),
  ...op("ObterArtista", (a) => repo.obterArtista(Number(a.id))),
  ...op("AlbunsDoArtista", (a) => repo.albunsDoArtista(Number(a.id)), lista("Album")),
  ...op("ObterAlbum", (a) => repo.obterAlbum(Number(a.id))),
  ...op("MusicasDoAlbum", (a) => repo.musicasDoAlbum(Number(a.id)), lista("Musica")),
};

// nomes de serviço e porta vêm do WSDL: <wsdl:service name="StreamingService"><wsdl:port name="Application">
const servicos = { StreamingService: { Application: operacoes } };

const http = createServer((_req, res) => { res.statusCode = 404; res.end(); });
http.listen(porta, () => {
  soap.listen(http, { path: "/", services: servicos, xml: wsdl });
  console.log(`SOAP (Node.js) ouvindo na porta ${porta}`);
});
