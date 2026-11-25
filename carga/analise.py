"""
Lê carga/resultados/*.json (saída do k6 --summary-export) e gera:
  carga/resultados/resumo.csv                 todas as execuções
  carga/graficos/vazao_<cenario>.png          vazão × usuários; Python e Node lado a lado
  carga/graficos/menor_carga_latencia.png     latência mediana com 1 usuário (menor carga)
  carga/graficos/maior_carga_vazao.png        vazão com 200 usuários (maior carga)
  carga/graficos/maior_carga_latencia.png     latência p95 com 200 usuários
  carga/graficos/bytes_por_operacao.png       tamanho da resposta por operação
  carga/resultados/destaques.txt              números usados na análise

Executar (na raiz do projeto):  python carga/analise.py
"""
import csv
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(BASE, "resultados")
OUT = os.path.join(BASE, "graficos")
os.makedirs(OUT, exist_ok=True)

LINGS = ["python", "node"]
TECS = ["rest", "graphql", "grpc", "soap"]
CENS = ["leve", "pesado", "aninhado", "escrita"]
NOME = {"rest": "REST", "graphql": "GraphQL", "grpc": "gRPC", "soap": "SOAP", "python": "Python", "node": "Node.js",
        "leve": "Leve", "pesado": "Pesado", "aninhado": "Aninhado", "escrita": "Escrita"}
DESC = {"leve": "músicas de uma playlist (20 itens)", "pesado": "página de 1.000 músicas",
        "aninhado": "playlists de um usuário + músicas de cada", "escrita": "criar playlist com 10 músicas"}
COR_TEC = {"rest": "#2a78d6", "graphql": "#eb6834", "grpc": "#1baf7a", "soap": "#eda100"}
MARCA = {"rest": "o", "graphql": "s", "grpc": "^", "soap": "D"}
COR_LING = {"python": "#5b4fc4", "node": "#d4552b"}

TINTA, TINTA2, GRADE = "#1f1f1e", "#5f5e58", "#e6e5e0"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.edgecolor": GRADE,
    "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRADE, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.dpi": 150, "savefig.bbox": "tight", "figure.facecolor": "white",
})
fmt = lambda v, casas=0: f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ------------------------------------------------------------------ leitura
dados = {}
for arq in glob.glob(os.path.join(RES, "*.json")):
    ling, tec, cen, vus = os.path.basename(arq)[:-5].split("_")
    m = json.load(open(arq))["metrics"]
    it, dur = m["iterations"], m["iteration_duration"]
    dados[(ling, tec, cen, int(vus))] = {
        "ops": it["rate"], "p50": dur["med"], "p95": dur["p(95)"], "p99": dur["p(99)"], "media": dur["avg"],
        "erro": m.get("erros", {}).get("value", 0), "bytes": m["data_received"]["count"] / it["count"],
        "n": it["count"],
    }
CARGAS = sorted({k[3] for k in dados})
MENOR, MAIOR = CARGAS[0], CARGAS[-1]

with open(os.path.join(RES, "resumo.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["linguagem", "tecnologia", "cenario", "usuarios", "ops_por_s", "lat_p50_ms", "lat_p95_ms",
                "lat_p99_ms", "taxa_erro", "bytes_por_op", "operacoes"])
    for (l, t, c, v), d in sorted(dados.items(), key=lambda kv: (LINGS.index(kv[0][0]), TECS.index(kv[0][1]),
                                                                  CENS.index(kv[0][2]), kv[0][3])):
        w.writerow([l, t, c, v, round(d["ops"], 3), round(d["p50"], 2), round(d["p95"], 2), round(d["p99"], 2),
                    d["erro"], round(d["bytes"]), d["n"]])

g = lambda l, t, c, v, campo: dados.get((l, t, c, v), {}).get(campo)


# ------------------------------------------------------------------ vazão × carga (small multiples)
def eixo_cargas(ax):
    ax.set_xscale("log")
    ax.set_xticks(CARGAS)
    ax.set_xticklabels([str(c) for c in CARGAS])
    ax.minorticks_off()
    ax.set_xlim(CARGAS[0] * 0.8, CARGAS[-1] * 1.9)


for cen in CENS:
    topo = max(g(l, t, cen, v, "ops") or 0 for l in LINGS for t in TECS for v in CARGAS)
    fig, axs = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, ling in zip(axs, LINGS):
        finais = []
        for tec in TECS:
            xs = [v for v in CARGAS if (ling, tec, cen, v) in dados]
            ys = [g(ling, tec, cen, v, "ops") for v in xs]
            if not xs:
                continue
            ax.plot(xs, ys, color=COR_TEC[tec], lw=2, marker=MARCA[tec], ms=7, markeredgecolor="white",
                    markeredgewidth=1.3, label=NOME[tec])
            finais.append((ys[-1], tec, xs[-1]))
        finais.sort()
        ultimo = -1e18
        for y, tec, x in finais:          # rótulos diretos sem colisão
            yl = max(y, ultimo + topo * 0.055)
            ultimo = yl
            ax.annotate(f"{NOME[tec]} {fmt(y)}", (x, yl), xytext=(8, 0), textcoords="offset points",
                        va="center", color=TINTA, fontsize=10.5)
        eixo_cargas(ax)
        ax.set_title(NOME[ling], loc="left", color=TINTA, fontsize=13)
        ax.set_xlabel("usuários virtuais simultâneos")
    axs[0].set_ylim(0, topo * 1.1)          # mesma escala nos dois painéis, começando em zero
    axs[0].set_ylabel("operações por segundo (maior é melhor)")
    axs[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt(v)))
    axs[0].legend(frameon=False, ncol=4, loc="upper left", bbox_to_anchor=(0, -0.13))
    fig.suptitle(f"{NOME[cen]}: {DESC[cen]}", x=0.01, ha="left", color=TINTA, fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"vazao_{cen}.png"))
    plt.close(fig)


# ------------------------------------------------------------------ barras agrupadas: tecnologia × linguagem
def barras(campo, carga, titulo, rotulo_y, arquivo, log=False, casas=0, sufixo=""):
    fig, axs = plt.subplots(1, 4, figsize=(16, 4.6))
    for ax, cen in zip(axs, CENS):
        larg = 0.38
        for i, ling in enumerate(LINGS):
            vals = [g(ling, t, cen, carga, campo) or 0 for t in TECS]
            xs = [k + (i - 0.5) * larg for k in range(len(TECS))]
            bs = ax.bar(xs, vals, width=larg, color=COR_LING[ling], edgecolor="white", linewidth=1.5,
                        label=NOME[ling])
            for b, v in zip(bs, vals):
                ax.annotate(fmt(v, casas) + sufixo, (b.get_x() + b.get_width() / 2, v), xytext=(0, 3),
                            textcoords="offset points", ha="center", fontsize=8.5, color=TINTA)
        ax.set_xticks(range(len(TECS)))
        ax.set_xticklabels([NOME[t] for t in TECS])
        ax.set_title(NOME[cen], loc="left", color=TINTA)
        ax.grid(axis="x", visible=False)
        if log:
            ax.set_yscale("log")
            ax.yaxis.set_minor_formatter(mticker.NullFormatter())
            ax.set_ylim(top=ax.get_ylim()[1] * 1.6)
        else:
            ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt(v, 0 if v >= 10 or v == int(v) else 1)))
    axs[0].set_ylabel(rotulo_y)
    axs[0].legend(frameon=False, loc="upper left", bbox_to_anchor=(0, -0.1), ncol=2)
    fig.suptitle(titulo, x=0.01, ha="left", color=TINTA, fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, arquivo))
    plt.close(fig)


barras("p50", MENOR, f"Menor carga ({MENOR} usuário): latência mediana por operação",
       "ms (menor é melhor)", "menor_carga_latencia.png", casas=1)
barras("ops", MENOR, f"Menor carga ({MENOR} usuário): operações por segundo",
       "op/s (maior é melhor)", "menor_carga_vazao.png")
barras("ops", MAIOR, f"Maior carga ({MAIOR} usuários): operações por segundo",
       "op/s (maior é melhor)", "maior_carga_vazao.png")
barras("p95", MAIOR, f"Maior carga ({MAIOR} usuários): latência p95",
       "ms, escala log (menor é melhor)", "maior_carga_latencia.png", log=True)
barras("bytes", MENOR, "Bytes recebidos por operação (inclui cabeçalhos)",
       "bytes, escala log", "bytes_por_operacao.png", log=True)

# ------------------------------------------------------------------ destaques em texto
linhas = []
P = linhas.append
for carga, rotulo in ((MENOR, "MENOR CARGA"), (MAIOR, "MAIOR CARGA")):
    P(f"\n===== {rotulo}: {carga} usuário(s) =====")
    for cen in CENS:
        P(f"\n-- {NOME[cen]} ({DESC[cen]})")
        P(f"{'':10}" + "".join(f"{NOME[t] + ' ' + NOME[l][:2]:>16}" for l in LINGS for t in TECS))
        for campo, nome_c in (("ops", "op/s"), ("p50", "p50 ms"), ("p95", "p95 ms")):
            P(f"{nome_c:10}" + "".join(f"{g(l, t, cen, carga, campo) or 0:>16.1f}" for l in LINGS for t in TECS))
        for l in LINGS:
            ordem = sorted(TECS, key=lambda t: -(g(l, t, cen, carga, "ops") or 0))
            P(f"ranking {NOME[l]}: " + " > ".join(f"{NOME[t]} ({g(l, t, cen, carga, 'ops'):.0f})" for t in ordem))
        P("Node/Python (vazão): " + ", ".join(
            f"{NOME[t]} {g('node', t, cen, carga, 'ops') / g('python', t, cen, carga, 'ops'):.2f}x" for t in TECS))
P("\n===== ESCALABILIDADE: vazão com a maior carga ÷ vazão com a menor =====")
for cen in CENS:
    P(f"{NOME[cen]:9}" + ", ".join(
        f"{NOME[t]}-{NOME[l][:2]} {g(l, t, cen, MAIOR, 'ops') / g(l, t, cen, MENOR, 'ops'):.1f}x"
        for l in LINGS for t in TECS))
P("\n===== BYTES POR OPERAÇÃO (1 usuário) =====")
for cen in CENS:
    P(f"{NOME[cen]:9}" + ", ".join(f"{NOME[t]}-{NOME[l][:2]} {g(l, t, cen, MENOR, 'bytes'):.0f}"
                                   for l in LINGS for t in TECS))
P(f"\nErros: máximo {max(d['erro'] for d in dados.values()):.4f}; execuções: {len(dados)}; "
  f"operações: {sum(d['n'] for d in dados.values())}")
texto = "\n".join(linhas)
open(os.path.join(RES, "destaques.txt"), "w", encoding="utf-8").write(texto)
print(texto)
