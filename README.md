# Trabalho 6: Comparação de Tecnologias de Invocação de Serviços Remotos

**Computação Distribuída · Unifor · Prof. Nabor C. Mendonça**
Equipe: Mateus Tomaz, Lucas Barros e Vitor Cesar

Este projeto implementa o mesmo **serviço de streaming de músicas** com as **4 tecnologias** do
enunciado (REST, GraphQL, gRPC e SOAP), em **2 linguagens** (Python e Node.js com TypeScript).
São **8 serviços**, todos ligados ao mesmo banco PostgreSQL. Eles foram comparados com testes
de carga para medir qual aguenta mais requisições, qual responde mais rápido e qual gera
menos tráfego.

> **Pressa?** Instale o Docker Desktop e vá direto para a
> [Opção A](#opção-a-tudo-com-docker-recomendado). São 3 comandos.

---

## Índice

1. [O que tem aqui](#1-o-que-tem-aqui)
2. [O que instalar](#2-o-que-instalar)
3. [Opção A: tudo com Docker (recomendado)](#opção-a-tudo-com-docker-recomendado)
4. [Opção B: banco no Docker, código na sua máquina](#opção-b-banco-no-docker-código-na-sua-máquina)
5. [Opção C: sem Docker](#opção-c-sem-docker)
6. [Como testar se está funcionando](#6-como-testar-se-está-funcionando)
7. [O CRUD e as consultas](#7-o-crud-e-as-consultas)
8. [Testes de carga](#8-testes-de-carga)
9. [Resultados que já estão no projeto](#9-resultados-que-já-estão-no-projeto)
10. [Estrutura das pastas](#10-estrutura-das-pastas)
11. [Problemas comuns](#11-problemas-comuns)
12. [Roteiro para a demonstração](#12-roteiro-para-a-demonstração)

---

## 1. O que tem aqui

### Os 8 serviços

| Tecnologia | Python (biblioteca · porta) | Node.js (biblioteca · porta) | Contrato que os dois seguem     |
|------------|-----------------------------|------------------------------|---------------------------------|
| REST       | FastAPI · **8001**          | Express · **9001**           | mesmas URIs e mesmo JSON        |
| GraphQL    | Strawberry · **8002**       | GraphQL Yoga · **9002**      | `contratos/streaming.graphql`   |
| SOAP 1.1   | Spyne · **8003**            | node-soap · **9003**         | `contratos/streaming.wsdl`      |
| gRPC       | grpcio · **50051**          | @grpc/grpc-js · **50052**    | `contratos/streaming.proto`     |

Regra fácil para lembrar: **Python usa as portas 800x e 50051; Node usa 900x e 50052.**

As duas linguagens seguem exatamente o mesmo contrato. Um cliente feito para o REST em Python
funciona no REST em Node só trocando a porta, e o mesmo vale para as outras tecnologias.
O teste funcional (seção 6) confirma que os 8 serviços devolvem dados idênticos.

### O banco de dados

PostgreSQL 16 com **7 tabelas**:

```
Artista 1 ── 0..* Álbum 1 ── 1..* Música *── 1 Gênero
Usuário 1 ── 0..* Playlist *── playlist_musica ──* Música
```

- **Do enunciado:** `usuarios`, `musicas` e `playlists`. A tabela `playlist_musica` liga playlists
  e músicas, porque uma playlist tem várias músicas e uma música pode estar em várias playlists.
- **Extras:** `artistas`, `albuns` e `generos`.

O banco é carregado automaticamente com **cerca de 752 mil registros**: 10.000 usuários,
100.000 músicas, 30.000 playlists, 600.000 ligações playlist-música, 10.000 álbuns, 2.000
artistas e 20 gêneros. Os dados são gerados com uma "semente" fixa (`banco/02_seed.sql`),
então qualquer computador tem exatamente os mesmos registros.

---

## 2. O que instalar

Depende de como você quer rodar:

| Você quer...                                         | Precisa instalar                                      |
|------------------------------------------------------|-------------------------------------------------------|
| **Só rodar e demonstrar** (Opção A)                  | Docker Desktop                                        |
| **Mexer no código** (Opção B)                        | Docker Desktop + Python 3.11 + Node.js 22             |
| **Rodar sem Docker** (Opção C)                       | PostgreSQL 16 + Python 3.11 + Node.js 22              |
| **Gerar os gráficos dos testes de carga**            | Python 3.11 (com as dependências do projeto)          |

### Docker Desktop
Baixe em https://www.docker.com/products/docker-desktop/ e instale. No Windows, ele pede para
ativar o WSL 2: aceite e reinicie o computador se ele pedir. Depois, **abra o Docker Desktop e
espere o ícone da baleia ficar estável** (“Engine running”). Os comandos `docker` só funcionam com
ele aberto.

### Python 3.11
**Tem que ser o 3.11.** A biblioteca do SOAP (Spyne) não funciona no 3.12 ou mais novo.
- Windows: instale pela Microsoft Store ("Python 3.11") ou por https://www.python.org/downloads/
  (no instalador, marque **"Add python.exe to PATH"**).
- Confira com `python --version` (deve mostrar `Python 3.11.x`).

### Node.js 22
Baixe a versão **22 LTS** em https://nodejs.org/. Precisa ser a **22.18 ou mais nova**: ela roda
TypeScript direto, sem etapa de compilação. Confira com `node --version`.

---

## Opção A: tudo com Docker (recomendado)

Sobe o banco e os 8 serviços sem instalar Python nem Node. No Windows, use o **PowerShell** ou o
**Prompt de Comando**.

**1. Abra o terminal na pasta do projeto** (a que tem o arquivo `docker-compose.yml`):

```powershell
cd C:\Users\SEU_USUARIO\Downloads\trabalho6-streaming-v2\trabalho6
dir          # deve listar docker-compose.yml, README.md, banco, python, node...
```

> Atenção: o zip tem uma pasta `trabalho6` **dentro** da pasta descompactada. É nela que você entra.

**2. Suba tudo:**

```powershell
docker compose up -d --build
```

- `--build` monta as imagens (só demora na **primeira vez**: de 3 a 10 minutos, porque baixa o
  Python, o Node e as bibliotecas).
- `-d` deixa rodando em segundo plano e devolve o terminal.
- Na primeira subida, o banco leva cerca de 15 a 30 segundos para criar as tabelas e carregar os
  dados. Os serviços esperam o banco ficar pronto antes de iniciar.

**3. Confira se está tudo no ar:**

```powershell
docker compose ps
```

Você deve ver 9 linhas (`db`, 4 `py-*` e 4 `node-*`), todas com `STATUS` `Up` (o banco aparece como
`healthy`).

**4. Rode o teste funcional** (as 6 consultas e o CRUD nos 8 serviços):

```powershell
docker compose run --rm testes
```

O resultado esperado termina com `RESULTADO: tudo certo`.

**5. Abra no navegador:**
- REST (Swagger): http://localhost:8001/docs
- GraphQL (GraphiQL): http://localhost:8002/graphql (Python) e http://localhost:9002/graphql (Node)

### Comandos úteis do Docker

| Para...                                         | Comando                                   |
|-------------------------------------------------|-------------------------------------------|
| Ver o log de um serviço (Ctrl+C para sair)      | `docker compose logs -f py-rest`          |
| Parar tudo (os dados do banco continuam)        | `docker compose stop`                     |
| Voltar a rodar depois de parar                  | `docker compose start`                    |
| Desligar e remover os containers                | `docker compose down`                     |
| Apagar tudo, **inclusive o banco**              | `docker compose down -v`                  |
| Subir só o banco                                | `docker compose up -d db`                 |

Os nomes dos serviços são: `db`, `py-rest`, `py-graphql`, `py-soap`, `py-grpc`, `node-rest`,
`node-graphql`, `node-soap` e `node-grpc`.

---

## Opção B: banco no Docker, código na sua máquina

Útil para mexer no código e ver a mudança na hora, sem reconstruir imagens. O banco roda no Docker
e os 8 serviços rodam direto no seu computador.

**1. Suba só o banco** (na pasta `trabalho6`):

```powershell
docker compose up -d db
```

Se os serviços da Opção A estiverem rodando, pare-os antes com `docker compose stop`, senão as
portas ficam ocupadas. O comando `docker compose up -d db` volta a subir só o banco.

**2. Crie o ambiente Python e instale as dependências** (só na primeira vez):

```powershell
python -m venv .venv
.venv\Scripts\activate                  # Mac/Linux: source .venv/bin/activate
pip install -r python\requirements.txt
```

Quando o ambiente está ativo, o terminal mostra `(.venv)` no começo da linha. **Toda vez que
abrir um terminal novo, ative de novo** com `.venv\Scripts\activate`.

> No PowerShell, se aparecer “a execução de scripts foi desabilitada”, rode uma vez
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, responda `S` e tente de novo.

**3. Instale as dependências do Node** (só na primeira vez):

```powershell
cd node
npm install
cd ..
```

**4. Suba os 8 serviços de uma vez** (com o `(.venv)` ativo, na pasta `trabalho6`):

```powershell
python iniciar_servicos.py
```

Em poucos segundos aparece `8 serviços no ar`. Deixe esse terminal aberto; **Ctrl+C** encerra
todos. Para subir só uma linguagem: `python iniciar_servicos.py python` ou
`python iniciar_servicos.py node`.

Se preferir um terminal por serviço, os comandos são:

```powershell
# na pasta python\ (com o .venv ativo)
uvicorn rest.servidor:app --port 8001
uvicorn graphql_svc.servidor:app --port 8002
uvicorn soap.servidor:app --port 8003
python -m grpc_svc.servidor

# na pasta node\
node src/rest.ts
node src/graphql.ts
node src/soap.ts
node src/grpc.ts
```

**5. Teste** num segundo terminal (com o `.venv` ativo):

```powershell
cd python
python -m clientes.teste_funcional              # as duas linguagens
python -m clientes.teste_funcional python       # só Python
python -m clientes.teste_funcional node         # só Node
```

---

## Opção C: sem Docker

Igual à Opção B, mas com o PostgreSQL 16 instalado direto no computador
(https://www.postgresql.org/download/). Depois de instalar, crie o usuário e o banco e carregue
os dados, na pasta `trabalho6`:

```powershell
psql -U postgres -c "CREATE USER streaming WITH PASSWORD 'streaming';"
psql -U postgres -c "CREATE DATABASE streaming OWNER streaming;"
psql -U streaming -d streaming -f banco/01_schema.sql
psql -U streaming -d streaming -f banco/02_seed.sql
```

Como esse banco tem senha, avise os serviços pela variável `DATABASE_URL` antes de subi-los:

```powershell
$env:DATABASE_URL = "postgresql://streaming:streaming@localhost:5432/streaming"   # PowerShell
set DATABASE_URL=postgresql://streaming:streaming@localhost:5432/streaming        # Prompt de Comando
```

Depois siga os passos 2 a 5 da Opção B, no mesmo terminal em que definiu a variável.

---

## 6. Como testar se está funcionando

### Teste funcional automático
`python -m clientes.teste_funcional` (Opção B/C) ou `docker compose run --rm testes` (Opção A).
Ele faz, nos 8 serviços:

1. As **5 consultas do enunciado** e uma consulta extra (álbuns de um artista), conferindo se os
   8 devolvem **exatamente os mesmos dados**.
2. O **CRUD completo**: cria um usuário e uma playlist para ele, consulta, altera o usuário,
   remove o usuário e confirma que a busca seguinte dá erro, porque ele não existe mais.
3. O **server streaming** do gRPC, que só existe nessa tecnologia.

Saída esperada (resumida):

```
OK  1. Usuários (1ª página): 100 itens (idênticos nos 8 serviços)
OK  2. Músicas (1ª página): 100 itens (idênticos nos 8 serviços)
OK  3. Playlists do usuário 7: 3 itens (idênticos nos 8 serviços)
OK  4. Músicas da playlist 5: 20 itens (idênticos nos 8 serviços)
OK  5. Playlists com a música 42: 12 itens (idênticos nos 8 serviços)
OK  6. Álbuns do artista 3 (extra): 5 itens (idênticos nos 8 serviços)
...
OK  REST (Python): criar/consultar/alterar/remover; erro esperado após remoção -> HTTPError
...
RESULTADO: tudo certo
```

Se aparecerem **tracebacks** (blocos de erro) nas janelas dos servidores GraphQL ou SOAP do
Python durante esse teste, **é normal**: é o passo em que o teste procura de propósito o usuário
que acabou de apagar.

### No navegador

- **Swagger do REST (Python):** http://localhost:8001/docs. Escolha uma operação, clique em
  **Try it out** e depois em **Execute**.
- **GraphiQL:** http://localhost:8002/graphql (Python) ou http://localhost:9002/graphql (Node).
  Cole uma consulta e clique no botão de executar, por exemplo:

  ```graphql
  { usuario(id: 7) { nome playlists { nome musicas { nome album { titulo artista { nome } } genero { nome } } } } }
  ```

- **WSDL do SOAP:** http://localhost:8003/?wsdl ou http://localhost:9003/?wsdl.
- **gRPC** não funciona no navegador (é uma limitação da tecnologia). Use o teste funcional.

### Pelo terminal (PowerShell)

```powershell
Invoke-RestMethod http://localhost:9001/usuarios/7/playlists                  # REST em Node
Invoke-RestMethod http://localhost:8001/playlists/5/musicas                   # REST em Python
Invoke-RestMethod -Method Post http://localhost:8001/usuarios `
  -ContentType "application/json" -Body '{"nome": "Mateus", "idade": 21}'    # criar usuário
```

---

## 7. O CRUD e as consultas

Os 8 serviços têm **CRUD completo** de usuários, músicas e playlists, e **leitura** de artistas,
álbuns e gêneros. As listagens são **paginadas**: `pagina` (padrão 1) e `tamanho` (padrão 100,
máximo 1.000), porque devolver 100 mil músicas de uma vez seria inviável.

### CRUD de usuários (músicas e playlists seguem o mesmo padrão)

| Operação         | REST                       | GraphQL                         | gRPC e SOAP          |
|------------------|----------------------------|---------------------------------|----------------------|
| Create           | `POST /usuarios`           | `mutation { criarUsuario }`     | `CriarUsuario`       |
| Read (todos)     | `GET /usuarios?pagina=1`   | `{ usuarios(pagina: 1) }`       | `ListarUsuarios`     |
| Read (um)        | `GET /usuarios/{id}`       | `{ usuario(id: 1) }`            | `ObterUsuario`       |
| Update           | `PATCH /usuarios/{id}`     | `mutation { atualizarUsuario }` | `AtualizarUsuario`   |
| Delete           | `DELETE /usuarios/{id}`    | `mutation { removerUsuario }`   | `RemoverUsuario`     |

Regras do diagrama que o banco garante:
- Remover um usuário **remove as playlists dele** (remoção em cascata).
- Uma playlist precisa ter **pelo menos 1 música**.

### As 5 consultas do enunciado (+1 extra)

| Consulta                         | REST                            | GraphQL                                      | gRPC / SOAP          |
|----------------------------------|---------------------------------|----------------------------------------------|----------------------|
| Todos os usuários                | `GET /usuarios`                 | `{ usuarios { id nome } }`                   | `ListarUsuarios`     |
| Todas as músicas                 | `GET /musicas`                  | `{ musicas { id nome } }`                    | `ListarMusicas`      |
| Playlists de um usuário          | `GET /usuarios/{id}/playlists`  | `{ usuario(id: 1) { playlists { nome } } }`  | `PlaylistsDoUsuario` |
| Músicas de uma playlist          | `GET /playlists/{id}/musicas`   | `{ playlist(id: 1) { musicas { nome } } }`   | `MusicasDaPlaylist`  |
| Playlists que contêm uma música  | `GET /musicas/{id}/playlists`   | `{ musica(id: 1) { playlists { nome } } }`   | `PlaylistsComMusica` |
| Álbuns de um artista (extra)     | `GET /artistas/{id}/albuns`     | `{ artista(id: 1) { albuns { titulo } } }`   | `AlbunsDoArtista`    |

### Como cada tecnologia avisa “não encontrado”

| Tecnologia | Resposta                                   |
|------------|--------------------------------------------|
| REST       | HTTP 404                                   |
| GraphQL    | HTTP 200, com o erro no campo `errors`     |
| gRPC       | status `NOT_FOUND`                         |
| SOAP       | HTTP 500 com um *SOAP Fault* (padrão do SOAP 1.1) |

---

## 8. Testes de carga

### O que é medido

A ferramenta é o [k6](https://k6.io). Ela fala HTTP e gRPC nativamente, então o mesmo gerador de
carga testa os 8 serviços. O script é `carga/teste_carga.js`.

**4 cenários**, cada um com IDs aleatórios a cada requisição:

| Cenário  | O que faz                                                    | Por que é interessante                          |
|----------|--------------------------------------------------------------|-------------------------------------------------|
| leve     | músicas de uma playlist (20 itens)                           | resposta pequena: mede o custo do protocolo     |
| pesado   | uma página de 1.000 músicas                                  | resposta grande: mede serialização e tamanho    |
| aninhado | playlists de um usuário + músicas de cada uma                | REST, gRPC e SOAP fazem 4 chamadas; GraphQL, 1  |
| escrita  | criar uma playlist com 10 músicas                            | grava no banco, numa transação                  |

**5 níveis de carga:** 1, 10, 50, 100 e 200 **usuários virtuais** simultâneos (cada um faz
requisições sem parar), por 20 segundos cada, depois de 3 segundos de aquecimento.

Total: 2 linguagens × 4 tecnologias × 4 cenários × 5 cargas = **160 execuções** (cerca de 1 hora).

**Métricas:** operações por segundo (vazão), latência (mediana, p95 e p99) e bytes recebidos por
operação. "p95 = 200 ms" quer dizer que 95% das requisições levaram até 200 ms.

### Rodando pelo Docker (Windows, Mac ou Linux)

Com os serviços no ar pela **Opção A** (`docker compose up -d --build`) e o Python instalado:

```powershell
python carga/bateria_docker.py
```

Ele roda as 160 execuções e salva um arquivo por execução em `carga/resultados/`. Para um teste
rápido, limite o que roda (exemplo no PowerShell):

```powershell
$env:CARGAS = "1 200"; $env:DUR = "10s"; python carga/bateria_docker.py
```

As variáveis disponíveis são `LINGS`, `TECS`, `CENARIOS`, `CARGAS` e `DUR`. Para ver os
comandos sem executar nada: `python carga/bateria_docker.py --mostrar`.

Para rodar **uma execução só** com o k6 do Docker:

```powershell
docker compose run --rm k6 run -e LING=node -e TEC=grpc -e CEN=leve -e VUS=50 -e DUR=20s /carga/teste_carga.js
```

### Rodando no Linux sem Docker (o método usado nos nossos resultados)

```bash
bash carga/executar_testes.sh
```

Esse script sobe **um serviço por vez** e usa o `taskset` para colocar o serviço e o banco num
núcleo da CPU e o k6 em outro, para que não disputem processador. Os números ficam mais justos.
Pelo Docker, os 8 serviços ficam ligados ao mesmo tempo, sem essa separação.

### Gerando os gráficos

Depois de qualquer uma das baterias (com o `.venv` ativo, na pasta `trabalho6`):

```powershell
python carga/analise.py
```

Isso gera:
- `carga/resultados/resumo.csv`: uma linha por execução, com todas as métricas.
- `carga/resultados/destaques.txt`: rankings, comparações Node × Python e escalabilidade, em texto.
- `carga/graficos/*.png`: os gráficos usados nos slides.

> Se você rodar uma bateria nova, os arquivos dela **substituem** os nossos em
> `carga/resultados/`. Faça uma cópia da pasta antes, se quiser guardar os originais.

### A "armadilha de medição"

No cenário pesado, o k6 faz o gRPC parecer mais lento do que é, porque gasta tempo convertendo
cada resposta protobuf em objetos JavaScript. O script `carga/medir_cliente_nativo.py` mede o
mesmo cenário com clientes Python nativos e mostra o gRPC mais rápido que o REST. Rode com os
serviços REST e gRPC no ar:

```powershell
cd python
python ..\carga\medir_cliente_nativo.py
```

---

## 9. Resultados que já estão no projeto

A pasta `carga/` já vem com a nossa bateria completa: 160 execuções, cerca de 1,5 milhão de
operações e **nenhum erro**. Ela foi rodada numa máquina Linux com 2 núcleos (Intel Xeon 2,1 GHz,
8 GB de RAM), usando `executar_testes.sh`.

Operações por segundo com 200 usuários (maior carga):

| Cenário  | REST Py | GraphQL Py | gRPC Py | SOAP Py | REST Node | GraphQL Node | gRPC Node | SOAP Node |
|----------|--------:|-----------:|--------:|--------:|----------:|-------------:|----------:|----------:|
| Leve     | 1.069   | 197        | 1.097   | 320     | 1.630     | 997          | 1.929     | 1.379     |
| Pesado   | 96      | 34         | 140     | 13      | 215       | 150          | 170       | 97        |
| Aninhado | 257     | 113        | 284     | 77      | 398       | 378          | 398       | 362       |
| Escrita  | 574     | 171        | 557     | 256     | 732       | 714          | 776       | 777       |

Resumo da análise (detalhada nos slides):
- **Menor carga (1 usuário):** no Python, o REST tem a menor latência em 3 cenários. No Node,
  as 4 tecnologias ficam próximas, e o GraphQL vence o cenário aninhado.
- **Maior carga (200 usuários):** o gRPC tem a maior vazão em 5 dos 8 casos. No Python, GraphQL e
  SOAP ficam bem atrás; no Node, a diferença entre as tecnologias é pequena.
- **Node × Python:** em REST e gRPC, quase empatam com 1 usuário e o Node abre vantagem sob carga.
  Em GraphQL e SOAP, o Node é de 1,6× a 6,8× mais rápido já com 1 usuário, por causa das
  bibliotecas Python.

---

## 10. Estrutura das pastas

```
trabalho6/
├── README.md                  este arquivo
├── docker-compose.yml         banco + 8 serviços + ferramentas (testes e k6)
├── iniciar_servicos.py        sobe os 8 serviços num terminal só (sem Docker)
│
├── banco/
│   ├── 01_schema.sql          cria as 7 tabelas e os índices
│   └── 02_seed.sql            gera os ~752 mil registros
│
├── contratos/                 contratos compartilhados pelas duas linguagens
│   ├── streaming.proto        gRPC
│   ├── streaming.wsdl         SOAP (gerado pelo Spyne)
│   └── streaming.graphql      GraphQL (gerado pelo Strawberry)
│
├── python/
│   ├── comum/dados.py         acesso ao banco (SQL), usado pelos 4 serviços
│   ├── rest/servidor.py       REST (FastAPI)
│   ├── graphql_svc/servidor.py GraphQL (Strawberry)
│   ├── soap/servidor.py       SOAP (Spyne)
│   ├── grpc_svc/servidor.py   gRPC (grpcio) + código gerado pelo protoc
│   ├── clientes/clientes.py   um cliente para cada tecnologia
│   ├── clientes/teste_funcional.py  teste dos 8 serviços
│   ├── requirements.txt
│   └── Dockerfile
│
├── node/
│   ├── src/dados.ts           acesso ao banco (mesmo SQL da versão Python)
│   ├── src/rest.ts            REST (Express)
│   ├── src/graphql.ts         GraphQL (GraphQL Yoga)
│   ├── src/soap.ts            SOAP (node-soap)
│   ├── src/grpc.ts            gRPC (@grpc/grpc-js)
│   ├── package.json
│   └── Dockerfile
│
└── carga/
    ├── teste_carga.js         script do k6 (4 cenários × 8 serviços)
    ├── bateria_docker.py      bateria completa pelo Docker (qualquer sistema)
    ├── executar_testes.sh     bateria completa no Linux, com núcleos separados
    ├── analise.py             gera resumo.csv, destaques.txt e gráficos
    ├── medir_cliente_nativo.py verificação da "armadilha de medição"
    ├── resultados/            um JSON por execução + resumo.csv + destaques.txt
    └── graficos/              gráficos PNG
```

Se você mudar o `streaming.proto`, gere de novo o código Python do gRPC (na pasta `python`):

```powershell
python -m grpc_tools.protoc -I ../contratos --python_out=grpc_svc --pyi_out=grpc_svc --grpc_python_out=grpc_svc ../contratos/streaming.proto
```

---

## 11. Problemas comuns

| Sintoma | Causa e solução |
|---------|-----------------|
| `'docker' não é reconhecido` ou `error during connect` | O Docker Desktop não está instalado ou não está aberto. Abra-o e espere aparecer “Engine running”. |
| `'py' não é reconhecido` / `'python' não é reconhecido` | Python não instalado ou fora do PATH. Instale o 3.11 (seção 2) e **abra um terminal novo**. |
| `No module named 'clientes'` (ou `rest`, `soap`...) | Você está na pasta errada. Os comandos `python -m ...` dos serviços e do teste rodam **dentro de `python\`**; `iniciar_servicos.py` roda na pasta `trabalho6`. |
| `No module named 'fastapi'` (ou outra biblioteca) | O ambiente virtual não está ativo (falta o `(.venv)` no começo da linha). Rode `.venv\Scripts\activate`. |
| Erro do Spyne envolvendo `six.moves` ou `ModuleNotFoundError: spyne.util.six.moves` | Você está no Python 3.12 ou mais novo. Use o **3.11** e recrie o `.venv`. |
| `ERRO: não consegui conectar ao banco` | O PostgreSQL não está no ar. Com Docker: `docker compose up -d db`. Sem Docker: confira se o serviço do PostgreSQL está rodando e se o `DATABASE_URL` está certo. |
| `address already in use` / `porta já em uso` | Outro programa (ou outra cópia do serviço) usa a porta. Pare a Opção A (`docker compose stop`) antes da B, ou feche o terminal antigo. |
| `Unknown file extension ".ts"` ao rodar `node src/...` | Node antigo. Instale o **22.18 ou mais novo** (`node --version`). |
| `docker compose ps` mostra um serviço `Restarting` | Veja o motivo com `docker compose logs py-rest` (troque pelo nome do serviço). |
| Quer recomeçar o banco do zero | `docker compose down -v` e depois `docker compose up -d --build`. |
| Tracebacks nas janelas do GraphQL/SOAP do Python durante o teste | Normal: é o teste buscando de propósito o usuário que acabou de remover. |

---

## 12. Roteiro para a demonstração

Cerca de 5 minutos, com tudo no ar pela Opção A:

1. **REST no Swagger** (http://localhost:8001/docs): `POST /usuarios` → `GET /usuarios/{id}` →
   `PATCH` → `DELETE` → `GET` de novo dá **404**. Mostra o CRUD com um verbo HTTP por operação.
2. **GraphQL no GraphiQL do Node** (http://localhost:9002/graphql): `criarUsuario`, depois uma
   consulta que navega usuário → playlists → músicas → álbum → artista **numa requisição só**, e
   `removerUsuario`. Mostra que o Node segue o mesmo contrato do Python.
3. **Os 8 no terminal:** `docker compose run --rm testes`. Prova o gRPC e o SOAP (que não têm
   interface no navegador) nas duas linguagens.

Antes de apresentar, aumente o zoom do navegador e a fonte do terminal (Ctrl + roda do mouse).
