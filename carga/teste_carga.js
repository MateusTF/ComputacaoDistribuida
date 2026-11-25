// Teste de carga das 8 implementações com k6 (https://k6.io).
//
// Uso:  k6 run -e LING=node -e TEC=grpc -e CEN=leve -e VUS=50 -e DUR=20s carga/teste_carga.js
//   LING: python | node
//   TEC:  rest | graphql | grpc | soap
//   CEN:  leve      -> músicas de uma playlist (20 itens, resposta pequena)
//         pesado    -> uma página de 1.000 músicas (resposta grande)
//         aninhado  -> playlists de um usuário + músicas de cada uma
//                      (REST/gRPC/SOAP fazem 4 chamadas; GraphQL resolve em 1)
//         escrita   -> cria uma playlist com 10 músicas (INSERT em transação)
//   HOST: onde estão os serviços (padrão localhost)
//
// Cada iteração = 1 operação completa do ponto de vista do cliente.
// Vazão = iterações/s; latência = iteration_duration.
import http from 'k6/http';
import grpc from 'k6/net/grpc';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const LING = __ENV.LING || 'python';
const TEC = __ENV.TEC || 'rest';
const CEN = __ENV.CEN || 'leve';
const HOST = __ENV.HOST || 'localhost';
const erros = new Rate('erros');

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DUR || '20s',
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

const PORTAS = {
  python: { rest: 8001, graphql: 8002, soap: 8003, grpc: 50051 },
  node:   { rest: 9001, graphql: 9002, soap: 9003, grpc: 50052 },
}[LING];
const REST = `http://${HOST}:${PORTAS.rest}`;
const GQL = `http://${HOST}:${PORTAS.graphql}/graphql`;
const SOAP = `http://${HOST}:${PORTAS.soap}/`;
const JSON_H = { headers: { 'Content-Type': 'application/json' } };
const XML_H = { headers: { 'Content-Type': 'text/xml; charset=utf-8' } };

const grpcClient = new grpc.Client();
grpcClient.load(['../contratos'], 'streaming.proto');
let conectado = false;

// volume do banco: 10.000 usuários, 100.000 músicas, 30.000 playlists
const rnd = (n) => 1 + Math.floor(Math.random() * n);
const dezMusicas = () => Array.from({ length: 10 }, () => rnd(100000));
const M = 'id nome duracaoSeg albumId generoId';

function ok(res) {
  const sucesso = TEC === 'grpc' ? res && res.status === grpc.StatusOK : (res.status === 200 || res.status === 201);
  erros.add(!sucesso);
  check(res, { 'sucesso': () => sucesso });
  return sucesso;
}

// ---------------- SOAP: envelopes montados à mão ----------------
function envelope(op, corpo) {
  return '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" ' +
         'xmlns:tns="urn:unifor:streaming"><soapenv:Body>' +
         `<tns:${op}>${corpo}</tns:${op}></soapenv:Body></soapenv:Envelope>`;
}
const soap = (op, corpo = '') => http.post(SOAP, envelope(op, corpo), XML_H);
const gql = (query, variables) => http.post(GQL, JSON.stringify({ query, variables }), JSON_H);

// ---------------- cenários por tecnologia ----------------
const impl = {
  rest: {
    leve: () => ok(http.get(`${REST}/playlists/${rnd(30000)}/musicas`)),
    pesado: () => ok(http.get(`${REST}/musicas?pagina=${rnd(100)}&tamanho=1000`)),
    aninhado: () => {
      const r = http.get(`${REST}/usuarios/${rnd(10000)}/playlists`);
      if (!ok(r)) return;
      for (const p of r.json()) ok(http.get(`${REST}/playlists/${p.id}/musicas`));
    },
    escrita: () => ok(http.post(`${REST}/usuarios/${rnd(10000)}/playlists`,
      JSON.stringify({ nome: 'Carga', musicas: dezMusicas() }), JSON_H)),
  },
  graphql: {
    leve: () => ok(gql(`query($id:Int!){ playlist(id:$id){ musicas { ${M} } } }`, { id: rnd(30000) })),
    pesado: () => ok(gql(`query($p:Int!){ musicas(pagina:$p, tamanho:1000){ ${M} } }`, { p: rnd(100) })),
    aninhado: () => ok(gql(`query($id:Int!){ usuario(id:$id){ playlists { id nome musicas { ${M} } } } }`,
      { id: rnd(10000) })),
    escrita: () => ok(gql('mutation($u:Int!,$m:[Int!]!){ criarPlaylist(nome:"Carga", usuarioId:$u, musicas:$m){ id } }',
      { u: rnd(10000), m: dezMusicas() })),
  },
  grpc: {
    leve: () => ok(grpcClient.invoke('streaming.Streaming/MusicasDaPlaylist', { id: rnd(30000) })),
    pesado: () => ok(grpcClient.invoke('streaming.Streaming/ListarMusicas', { pagina: rnd(100), tamanho: 1000 })),
    aninhado: () => {
      const r = grpcClient.invoke('streaming.Streaming/PlaylistsDoUsuario', { id: rnd(10000) });
      if (!ok(r)) return;
      for (const p of r.message.playlists || [])
        ok(grpcClient.invoke('streaming.Streaming/MusicasDaPlaylist', { id: p.id }));
    },
    escrita: () => ok(grpcClient.invoke('streaming.Streaming/CriarPlaylist',
      { nome: 'Carga', usuario_id: rnd(10000), musicas: dezMusicas() })),
  },
  soap: {
    leve: () => ok(soap('MusicasDaPlaylist', `<tns:id>${rnd(30000)}</tns:id>`)),
    pesado: () => ok(soap('ListarMusicas', `<tns:pagina>${rnd(100)}</tns:pagina><tns:tamanho>1000</tns:tamanho>`)),
    aninhado: () => {
      const r = soap('PlaylistsDoUsuario', `<tns:id>${rnd(10000)}</tns:id>`);
      if (!ok(r)) return;
      // aceita "<tns:Playlist><tns:id>" (Spyne) e "<Playlist><id>" (node-soap)
      const ids = [...r.body.matchAll(/<(?:tns:)?Playlist><(?:tns:)?id>(\d+)</g)].map((m) => m[1]);
      for (const id of ids) ok(soap('MusicasDaPlaylist', `<tns:id>${id}</tns:id>`));
    },
    escrita: () => ok(soap('CriarPlaylist', `<tns:nome>Carga</tns:nome><tns:usuario_id>${rnd(10000)}</tns:usuario_id>` +
      `<tns:musicas>${dezMusicas().map((m) => `<tns:integer>${m}</tns:integer>`).join('')}</tns:musicas>`)),
  },
};

export default function () {
  if (TEC === 'grpc' && !conectado) {
    grpcClient.connect(`${HOST}:${PORTAS.grpc}`, { plaintext: true });
    conectado = true;
  }
  impl[TEC][CEN]();
}
