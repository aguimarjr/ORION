# utilitário para salvar/imprimir fronteira de Pareto (NSGA2)
# Coloque este arquivo em: system/src/scheduler/include/pareto_plot.py

import os
import datetime
import matplotlib
# usa Agg para ambientes sem display (servidor)
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D  # necessário para 3D plots (mesmo que não referenciado diretamente)

def get_pareto_indices(objectives):
    """
    Recebe objectives: lista de listas/tuplas [obj1, obj2, ...] (minimizar).
    Retorna índices não dominados (fronteira de Pareto).
    Implementação simples O(n^2).
    """
    objs = [tuple(o) for o in objectives]
    n = len(objs)
    pareto = []
    for i in range(n):
        dominated = False
        a = objs[i]
        for j in range(n):
            if i == j:
                continue
            b = objs[j]
            if all(bk <= ak for bk, ak in zip(b, a)) and any(bk < ak for bk, ak in zip(b, a)):
                dominated = True
                break
        if not dominated:
            pareto.append(i)
    return pareto

def save_pareto_plot(objectives, ids=None, out_dir="system/output/pareto_plots", prefix="nsga2"):
    """
    Salva PNG e imprime no stdout (2D scatter usando as duas primeiras dimensões).
    - objectives: lista de [obj1, obj2, ...]
    - ids: lista de ids correspondentes (opcional)
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = os.path.join(out_dir, f"{prefix}_pareto_{ts}.png")

    df = pd.DataFrame(objectives)
    if df.shape[1] < 2:
        raise ValueError("Esperado pelo menos 2 objetivos para plot (obj1, obj2).")
    df = df.rename(columns={0: "obj1", 1: "obj2"})
    if ids is not None:
        df["id"] = ids
    else:
        df["id"] = df.index.astype(str)

    pareto_idx = get_pareto_indices(df[["obj1", "obj2"]].values.tolist())
    pareto_df = df.iloc[pareto_idx].reset_index(drop=True)

    # imprime tabela da fronteira no stdout
    print("=== Pareto front (obj1, obj2) com ids ===")
    for i, row in pareto_df.iterrows():
        print(f"{i}: id={row['id']}  obj1={row['obj1']}  obj2={row['obj2']}")

    # plot: todos em cinza, fronteira em vermelho com ids anotados
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(6, 4))
    plt.scatter(df["obj1"], df["obj2"], c="lightgray", label="all")
    plt.scatter(pareto_df["obj1"], pareto_df["obj2"], c="red", label="pareto", zorder=3)
    for _, row in pareto_df.iterrows():
        plt.annotate(str(row["id"]), (row["obj1"], row["obj2"]), textcoords="offset points", xytext=(4,4), fontsize=7)
    plt.xlabel("obj1")
    plt.ylabel("obj2")
    plt.title("Pareto front (NSGA2)")
    plt.legend()
    plt.grid(alpha=0.4, linestyle="--")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()

    print(f"Pareto plot salvo em: {filename}")
    return filename, pareto_df

def save_pareto_plot_3d(objectives, ids=None, out_dir="system/output/pareto_plots", prefix="nsga2_3d"):
    """
    Gera um scatter 3D (obj0 x obj1 x obj2) e destaca a fronteira de Pareto.
    - objectives: lista de tripletas [obj0, obj1, obj2] (minimizar)
    - ids: lista de ids correspondentes (opcional)
    Retorna (filepath, pareto_df) onde pareto_df contém as triples da fronteira.
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = os.path.join(out_dir, f"{prefix}_pareto3d_{ts}.png")

    # espera pelo menos 3 objetivos por solução
    df = pd.DataFrame(objectives)
    if df.shape[1] < 3:
        raise ValueError("Esperado pelo menos 3 objetivos para plot 3D (obj0, obj1, obj2).")
    df = df.rename(columns={0: "obj0", 1: "obj1", 2: "obj2"})
    if ids is not None:
        df["id"] = ids
    else:
        df["id"] = df.index.astype(str)

    # calcula fronteira de Pareto (usando as 3 dimensões)
    pareto_idx = get_pareto_indices(df[["obj0", "obj1", "obj2"]].values.tolist())
    pareto_df = df.iloc[pareto_idx].reset_index(drop=True)

    # imprime tabela da fronteira no stdout
    print("=== Pareto front 3D (obj0, obj1, obj2) com ids ===")
    for i, row in pareto_df.iterrows():
        print(f"{i}: id={row['id']}  obj0={row['obj0']}  obj1={row['obj1']}  obj2={row['obj2']}")

    # plot 3D
    sns.set_theme(style="whitegrid")
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    xs = df["obj0"].values
    ys = df["obj1"].values
    zs = df["obj2"].values

    # todos os pontos em cinza
    ax.scatter(xs, ys, zs, c="lightgray", s=20, depthshade=True, label="all")

    # fronteira em vermelho e maior
    px = pareto_df["obj0"].values
    py = pareto_df["obj1"].values
    pz = pareto_df["obj2"].values
    ax.scatter(px, py, pz, c="red", s=40, label="pareto", depthshade=True, zorder=5)

    # anotar ids da fronteira (leves offsets no eixo z para legibilidade)
    for _, row in pareto_df.iterrows():
        ax.text(row["obj0"], row["obj1"], row["obj2"], str(row["id"]), size=7, zorder=10)

    ax.set_xlabel("obj0 (avg_latency)")
    ax.set_ylabel("obj1 (violation_rate)")
    ax.set_zlabel("obj2 (imbalance)")
    ax.set_title("Pareto front (3D) - NSGA2")
    ax.legend(loc='best')

    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()

    print(f"Pareto 3D salvo em: {filename}")
    return filename, pareto_df