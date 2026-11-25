#!/usr/bin/env bash
# Bateria completa de testes de carga: 2 linguagens × 4 tecnologias × 4 cenários × 5 cargas.
#
# Cada servidor roda SOZINHO. Servidor e PostgreSQL ficam presos ao núcleo 0 da CPU e o k6 ao
# núcleo 1 (taskset), para que o gerador de carga não dispute processador com o sistema testado.
#
# Requisitos: Linux, k6, psql, PostgreSQL com o banco carregado (banco/*.sql),
#             ambiente Python (.venv na raiz) e node_modules instalados em node/.
# Uso (na raiz do projeto):  bash carga/executar_testes.sh
# Parcial:  LINGS="node" TECS="rest grpc" CENARIOS="leve" CARGAS="1 200" DUR=10s bash carga/executar_testes.sh
set -u
cd "$(dirname "$0")/.."
RAIZ=$(pwd)
PY=${PY:-$RAIZ/.venv/bin/python}
UV=${UV:-$RAIZ/.venv/bin/uvicorn}
DB=${DATABASE_URL:-postgresql://streaming@localhost:5432/streaming}
LINGS="${LINGS:-python node}"
TECS="${TECS:-rest graphql grpc soap}"
CENARIOS="${CENARIOS:-leve pesado aninhado escrita}"
CARGAS="${CARGAS:-1 10 50 100 200}"
DUR="${DUR:-20s}"
OUT=carga/resultados
mkdir -p "$OUT"

NUCLEO_SERV="taskset -c 0"; NUCLEO_K6="taskset -c 1"
command -v taskset >/dev/null || { NUCLEO_SERV=""; NUCLEO_K6=""; }

parar_todos() {
  pkill -f "uvicorn .*servidor:app" 2>/dev/null; pkill -f "grpc_svc.servidor" 2>/dev/null
  pkill -f "node src/(rest|graphql|grpc|soap).ts" 2>/dev/null; sleep 1
}

# prende o PostgreSQL (processo principal e conexões futuras) ao núcleo 0
PG=$(pgrep -o -x postgres || true)
[ -n "$PG" ] && [ -n "$NUCLEO_SERV" ] && taskset -a -p -c 0 "$PG" >/dev/null

iniciar() {   # $1 = linguagem, $2 = tecnologia
  case "$1-$2" in
    python-rest)    (cd python && DATABASE_URL=$DB $NUCLEO_SERV $UV rest.servidor:app        --port 8001 --log-level warning) & ;;
    python-graphql) (cd python && DATABASE_URL=$DB $NUCLEO_SERV $UV graphql_svc.servidor:app --port 8002 --log-level warning) & ;;
    python-soap)    (cd python && DATABASE_URL=$DB $NUCLEO_SERV $UV soap.servidor:app        --port 8003 --log-level warning) & ;;
    python-grpc)    (cd python && DATABASE_URL=$DB $NUCLEO_SERV $PY -m grpc_svc.servidor) & ;;
    node-*)         (cd node && DATABASE_URL=$DB $NUCLEO_SERV node src/$2.ts) & ;;
  esac
  sleep 4
}

limpar_escritas() {  # remove as playlists criadas pelo cenário de escrita
  psql -q "$DB" -c "DELETE FROM playlists WHERE id > 30000" -c "DELETE FROM usuarios WHERE id > 10000" \
               -c "VACUUM ANALYZE playlists, playlist_musica" >/dev/null
}

parar_todos
limpar_escritas
for ling in $LINGS; do
  for tec in $TECS; do
    iniciar "$ling" "$tec"
    for cen in $CENARIOS; do
      (cd carga && $NUCLEO_K6 k6 run -q -e LING=$ling -e TEC=$tec -e CEN=$cen -e VUS=5 -e DUR=3s teste_carga.js >/dev/null 2>&1)
      for vus in $CARGAS; do
        echo "$(date +%T) $ling $tec $cen vus=$vus"
        (cd carga && $NUCLEO_K6 k6 run -q -e LING=$ling -e TEC=$tec -e CEN=$cen -e VUS=$vus -e DUR=$DUR \
           --summary-export "resultados/${ling}_${tec}_${cen}_${vus}.json" teste_carga.js >/dev/null 2>&1)
      done
      [ "$cen" = escrita ] && limpar_escritas
    done
    parar_todos
  done
done
echo "FIM"
