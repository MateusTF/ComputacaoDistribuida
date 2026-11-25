/**
 * Serviço de streaming de músicas — REST (Node.js + Express).
 * Mesmas URIs, verbos, códigos de status e JSON da versão Python (FastAPI).
 *
 * Executar (na pasta node/):  node src/rest.ts        (porta 9001; mude com PORTA=...)
 */
import express, { type NextFunction, type Request, type Response } from "express";
import { ErroNaoEncontrado, ErroValidacao, novoRepositorio } from "./dados.ts";

const repo = novoRepositorio();
const app = express();
app.use(express.json());

const id = (req: Request) => Number(req.params.id);
const pag = (req: Request): [number, number] => [Number(req.query.pagina ?? 1), Number(req.query.tamanho ?? 100)];

/** Envolve um handler assíncrono e encaminha erros ao tratador central. */
const h = (fn: (req: Request, res: Response) => Promise<unknown>) =>
  (req: Request, res: Response, next: NextFunction) => {
    fn(req, res).then((corpo) => {
      if (res.headersSent) return;
      corpo === undefined ? res.status(204).end() : res.json(corpo);
    }).catch(next);
  };

const criado = (res: Response, corpo: unknown) => { res.status(201).json(corpo); };

// ---------- /usuarios ----------
app.get("/usuarios", h((req) => repo.listarUsuarios(...pag(req))));
app.get("/usuarios/:id", h((req) => repo.obterUsuario(id(req))));
app.post("/usuarios", h(async (req, res) => criado(res, await repo.criarUsuario(req.body.nome, req.body.idade))));
app.patch("/usuarios/:id", h((req) => repo.atualizarUsuario(id(req), req.body.nome, req.body.idade)));
app.delete("/usuarios/:id", h(async (req) => { await repo.removerUsuario(id(req)); }));
app.get("/usuarios/:id/playlists", h((req) => repo.playlistsDoUsuario(id(req))));            // consulta do enunciado
app.post("/usuarios/:id/playlists", h(async (req, res) =>
  criado(res, await repo.criarPlaylist(req.body.nome, id(req), req.body.musicas))));

// ---------- /musicas ----------
app.get("/musicas", h((req) => repo.listarMusicas(...pag(req))));
app.get("/musicas/:id", h((req) => repo.obterMusica(id(req))));
app.post("/musicas", h(async (req, res) => {
  const b = req.body;
  criado(res, await repo.criarMusica(b.nome, b.duracao_seg, b.album_id, b.genero_id));
}));
app.patch("/musicas/:id", h((req) => {
  const b = req.body;
  return repo.atualizarMusica(id(req), b.nome, b.duracao_seg, b.album_id, b.genero_id);
}));
app.delete("/musicas/:id", h(async (req) => { await repo.removerMusica(id(req)); }));
app.get("/musicas/:id/playlists", h((req) => repo.playlistsComMusica(id(req))));             // consulta do enunciado

// ---------- /playlists ----------
app.get("/playlists", h((req) => repo.listarPlaylists(...pag(req))));
app.get("/playlists/:id", h((req) => repo.obterPlaylist(id(req))));
app.patch("/playlists/:id", h((req) => repo.atualizarPlaylist(id(req), req.body.nome, req.body.musicas)));
app.delete("/playlists/:id", h(async (req) => { await repo.removerPlaylist(id(req)); }));
app.get("/playlists/:id/musicas", h((req) => repo.musicasDaPlaylist(id(req))));              // consulta do enunciado

// ---------- entidades extras (leitura) ----------
app.get("/generos", h(() => repo.listarGeneros()));
app.get("/generos/:id", h((req) => repo.obterGenero(id(req))));
app.get("/artistas", h((req) => repo.listarArtistas(...pag(req))));
app.get("/artistas/:id", h((req) => repo.obterArtista(id(req))));
app.get("/artistas/:id/albuns", h((req) => repo.albunsDoArtista(id(req))));
app.get("/albuns/:id", h((req) => repo.obterAlbum(id(req))));
app.get("/albuns/:id/musicas", h((req) => repo.musicasDoAlbum(id(req))));

// ---------- erros: mesmo formato da versão FastAPI ({"detail": ...}) ----------
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  if (err instanceof ErroNaoEncontrado) return res.status(404).json({ detail: err.message });
  if (err instanceof ErroValidacao) return res.status(422).json({ detail: err.message });
  console.error(err);
  res.status(500).json({ detail: "Erro interno" });
});

const porta = Number(process.env.PORTA ?? 9001);
app.listen(porta, () => console.log(`REST (Node.js) ouvindo na porta ${porta}`));
