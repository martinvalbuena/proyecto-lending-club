"""
EDA inicial — Lending Club.

Genera figuras y estadísticas descriptivas a partir de la muestra
estratificada (200K) y las guarda en:
  - paper/figures/eda_*.png      (para el paper)
  - results/eda_stats.json        (tablas resumen)
  - results/eda_report.md         (reporte narrativo auto-generado)

Uso:
    python src/eda.py
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SAMPLE_PATH = "data/processed/sample_200k.parquet"
FIG_DIR = "paper/figures"
RESULTS_DIR = "results"

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    return path


def fmt_pct(x, _=None):
    return f"{100*x:.1f}%"


def main():
    stats = {}
    figures = []

    # -----------------------------------------------------------------------
    # Carga
    # -----------------------------------------------------------------------
    df = pd.read_parquet(SAMPLE_PATH)
    print(f"Cargadas {len(df):,} filas × {df.shape[1]} columnas de {SAMPLE_PATH}")

    # Parseo de fechas
    df["issue_d"] = pd.to_datetime(df["issue_d"], format="%b-%Y", errors="coerce")
    df["issue_year"] = df["issue_d"].dt.year
    df["earliest_cr_line"] = pd.to_datetime(df["earliest_cr_line"], format="%b-%Y", errors="coerce")
    df["credit_history_yrs"] = (df["issue_d"] - df["earliest_cr_line"]).dt.days / 365.25

    # int_rate viene como string "13.99%", limpio si hace falta
    if df["int_rate"].dtype == object:
        df["int_rate"] = df["int_rate"].str.rstrip("%").astype(float)
    if df["revol_util"].dtype == object:
        df["revol_util"] = df["revol_util"].str.rstrip("%").astype(float)
    if df["term"].dtype == object:
        df["term_months"] = df["term"].str.extract(r"(\d+)").astype(float)

    # FICO promedio al origen
    df["fico_avg"] = (df["fico_range_low"] + df["fico_range_high"]) / 2

    # -----------------------------------------------------------------------
    # 1. Shape y calidad
    # -----------------------------------------------------------------------
    stats["shape"] = {"rows": len(df), "cols": df.shape[1]}
    stats["default_rate"] = float(df["default"].mean())

    null_rates = df.isna().mean().sort_values(ascending=False)
    stats["null_rates_top15"] = null_rates.head(15).round(4).to_dict()
    stats["null_rates_cols_with_any_null"] = int((null_rates > 0).sum())

    # Figura: null matrix (top 25 cols con más nulos)
    top_nulls = null_rates[null_rates > 0].head(25)
    if len(top_nulls) > 0:
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(y=top_nulls.index, x=top_nulls.values, ax=ax, color="steelblue")
        ax.set_xlabel("Proporción de valores nulos")
        ax.set_ylabel("")
        ax.set_title("Columnas con valores nulos (top 25)")
        ax.xaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
        figures.append(save(fig, "eda_nulls.png"))

    # -----------------------------------------------------------------------
    # 2. Target: default rates por dimensión categórica
    # -----------------------------------------------------------------------
    def default_rate_by(col, min_count=100):
        g = df.groupby(col)["default"].agg(["mean", "count"]).reset_index()
        g = g[g["count"] >= min_count].sort_values("mean")
        return g

    # Por grade
    g_grade = default_rate_by("grade")
    stats["default_rate_by_grade"] = g_grade.set_index("grade")["mean"].round(4).to_dict()

    fig, ax = plt.subplots(figsize=(6, 3.5))
    g = df.groupby("grade")["default"].mean().sort_index()
    n = df.groupby("grade").size()
    bars = ax.bar(g.index, g.values, color="steelblue", edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Tasa de default")
    ax.set_xlabel("Grade (Lending Club)")
    ax.set_title("Tasa de default por grade")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
    for bar, val, cnt in zip(bars, g.values, n.values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
                f"{100*val:.1f}%\nn={cnt/1000:.0f}K",
                ha="center", va="bottom", fontsize=7.5)
    ax.set_ylim(0, max(g.values) * 1.25)
    figures.append(save(fig, "eda_default_by_grade.png"))

    # Por sub_grade
    fig, ax = plt.subplots(figsize=(10, 3.5))
    g = df.groupby("sub_grade")["default"].mean().sort_index()
    ax.bar(g.index, g.values, color="steelblue", edgecolor="black", linewidth=0.3)
    ax.set_ylabel("Tasa de default")
    ax.set_xlabel("Sub-grade")
    ax.set_title("Tasa de default por sub_grade")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    figures.append(save(fig, "eda_default_by_subgrade.png"))

    # Por purpose
    g = df.groupby("purpose")["default"].agg(["mean", "count"]).sort_values("mean")
    g = g[g["count"] >= 200]
    stats["default_rate_by_purpose"] = g["mean"].round(4).to_dict()

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.barplot(y=g.index, x=g["mean"].values, ax=ax, color="steelblue")
    ax.set_xlabel("Tasa de default")
    ax.set_ylabel("")
    ax.set_title("Tasa de default por propósito del préstamo")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
    figures.append(save(fig, "eda_default_by_purpose.png"))

    # Por home_ownership
    g = df.groupby("home_ownership")["default"].agg(["mean", "count"])
    g = g[g["count"] >= 100].sort_values("mean")
    stats["default_rate_by_home_ownership"] = g["mean"].round(4).to_dict()

    # Por addr_state (heatmap USA)
    g_state = df.groupby("addr_state")["default"].agg(["mean", "count"]).reset_index()
    g_state = g_state[g_state["count"] >= 100].sort_values("mean", ascending=False)
    stats["default_rate_by_state_top5"] = g_state.head(5).set_index("addr_state")["mean"].round(4).to_dict()
    stats["default_rate_by_state_bottom5"] = g_state.tail(5).set_index("addr_state")["mean"].round(4).to_dict()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    sns.barplot(y=g_state.head(10)["addr_state"], x=g_state.head(10)["mean"],
                ax=axes[0], color="crimson")
    axes[0].set_title("Top 10 estados con más default")
    axes[0].set_xlabel("Tasa de default")
    axes[0].set_ylabel("")
    axes[0].xaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))

    sns.barplot(y=g_state.tail(10)["addr_state"][::-1], x=g_state.tail(10)["mean"][::-1],
                ax=axes[1], color="seagreen")
    axes[1].set_title("Bottom 10 estados con menos default")
    axes[1].set_xlabel("Tasa de default")
    axes[1].set_ylabel("")
    axes[1].xaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
    fig.suptitle("Heterogeneidad geográfica del default", y=1.02)
    figures.append(save(fig, "eda_default_by_state.png"))

    # -----------------------------------------------------------------------
    # 3. Continuous features condicional a default
    # -----------------------------------------------------------------------
    continuous_vars = {
        "int_rate": ("Tasa de interés (%)", False),
        "annual_inc": ("Ingreso anual (USD)", True),  # log scale
        "dti": ("DTI (%)", False),
        "fico_avg": ("FICO promedio al origen", False),
        "revol_util": ("Utilización revolvente (%)", False),
        "loan_amnt": ("Monto del préstamo (USD)", False),
    }
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for ax, (col, (label, log_x)) in zip(axes.flat, continuous_vars.items()):
        s = df[[col, "default"]].dropna()
        # Recorto outliers del 1% superior para visualización
        cap = s[col].quantile(0.99)
        s = s[s[col] <= cap]
        for d, color, lbl in [(0, "seagreen", "No default"), (1, "crimson", "Default")]:
            sns.kdeplot(s.loc[s["default"] == d, col], ax=ax, color=color,
                        fill=True, alpha=0.35, linewidth=1.2, label=lbl,
                        log_scale=log_x)
        ax.set_xlabel(label)
        ax.set_ylabel("")
        ax.set_title(col)
    axes[0, 0].legend(loc="upper right", frameon=True)
    fig.suptitle("Distribuciones condicionales: No default vs Default", y=1.0)
    fig.tight_layout()
    figures.append(save(fig, "eda_continuous_by_default.png"))

    # Medias por grupo
    cont_stats = (df.groupby("default")[list(continuous_vars.keys())]
                    .mean().round(2).to_dict(orient="index"))
    stats["continuous_means_by_default"] = cont_stats

    # -----------------------------------------------------------------------
    # 4. Temporal patterns
    # -----------------------------------------------------------------------
    yearly = df.groupby("issue_year").agg(
        volume=("default", "count"),
        default_rate=("default", "mean"),
        mean_int_rate=("int_rate", "mean"),
    ).dropna()

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.5))
    axes[0].bar(yearly.index.astype(int), yearly["volume"], color="steelblue", edgecolor="black", linewidth=0.3)
    axes[0].set_title("Volumen de préstamos emitidos por año")
    axes[0].set_xlabel("Año de emisión")
    axes[0].set_ylabel("N° préstamos (muestra)")

    axes[1].plot(yearly.index.astype(int), yearly["default_rate"], "o-", color="crimson", label="Tasa default")
    axes[1].plot(yearly.index.astype(int), yearly["mean_int_rate"]/100, "s-", color="steelblue", label="Tasa interés media")
    axes[1].set_title("Default rate vs tasa de interés media por año")
    axes[1].set_xlabel("Año de emisión")
    axes[1].set_ylabel("Proporción")
    axes[1].yaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
    axes[1].legend()
    fig.tight_layout()
    figures.append(save(fig, "eda_temporal.png"))

    stats["temporal"] = yearly.round(4).to_dict(orient="index")

    # -----------------------------------------------------------------------
    # 5. Pricing structure — el gráfico clave para la hipótesis H1
    # -----------------------------------------------------------------------
    # Tasa de interés vs tasa realizada de default por grade
    pricing = df.groupby("grade").agg(
        mean_int_rate=("int_rate", "mean"),
        default_rate=("default", "mean"),
        n=("default", "count"),
    ).sort_index()
    stats["pricing_by_grade"] = pricing.round(4).to_dict(orient="index")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(pricing))
    width = 0.38
    ax.bar(x - width/2, pricing["mean_int_rate"]/100, width, color="steelblue",
           label="Tasa de interés media (LC)", edgecolor="black", linewidth=0.4)
    ax.bar(x + width/2, pricing["default_rate"], width, color="crimson",
           label="Tasa de default realizada", edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(pricing.index)
    ax.set_xlabel("Grade (Lending Club)")
    ax.set_ylabel("Proporción")
    ax.set_title("Pricing (tasa interés) vs riesgo realizado (default) por grade")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
    ax.legend()
    figures.append(save(fig, "eda_pricing_vs_default_by_grade.png"))

    # Scatter int_rate vs default probability bin
    fig, ax = plt.subplots(figsize=(6, 4.5))
    df_plot = df[["int_rate", "default"]].dropna()
    df_plot["rate_bin"] = pd.cut(df_plot["int_rate"], bins=20)
    binned = df_plot.groupby("rate_bin").agg(
        mid=("int_rate", "mean"),
        default=("default", "mean"),
        n=("default", "count"),
    )
    ax.scatter(binned["mid"], binned["default"], s=binned["n"]/50,
               color="steelblue", alpha=0.65, edgecolor="black")
    ax.plot([0, binned["mid"].max()], [0, binned["mid"].max()/100], "k--",
            alpha=0.4, label="Línea 45° (pricing = riesgo)")
    ax.set_xlabel("Tasa de interés (%)")
    ax.set_ylabel("Tasa de default realizada")
    ax.set_title("¿La tasa de interés predice el default?\nTamaño del punto ∝ volumen")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt_pct))
    ax.legend()
    figures.append(save(fig, "eda_pricing_risk_scatter.png"))

    # -----------------------------------------------------------------------
    # Guardado de stats y reporte
    # -----------------------------------------------------------------------
    def _default(o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        if pd.isna(o): return None
        return str(o)

    with open(f"{RESULTS_DIR}/eda_stats.json", "w") as f:
        json.dump(stats, f, indent=2, default=_default)

    # Reporte markdown
    lines = []
    lines.append("# EDA inicial — Lending Club\n")
    lines.append(f"Muestra estratificada: **{stats['shape']['rows']:,} filas × {stats['shape']['cols']} columnas**.\n")
    lines.append(f"Tasa base de default: **{stats['default_rate']*100:.2f}%**.\n\n")

    lines.append("## Default rate por grade\n")
    lines.append("| Grade | Default rate |\n|---|---|\n")
    for k, v in sorted(stats["default_rate_by_grade"].items()):
        lines.append(f"| {k} | {v*100:.2f}% |\n")

    lines.append("\n## Pricing vs riesgo por grade\n")
    lines.append("| Grade | Tasa interés media | Default rate | N |\n|---|---|---|---|\n")
    for k, v in sorted(stats["pricing_by_grade"].items()):
        lines.append(f"| {k} | {v['mean_int_rate']:.2f}% | {v['default_rate']*100:.2f}% | {int(v['n']):,} |\n")

    lines.append("\n## Top 5 estados con mayor default rate\n")
    for k, v in stats["default_rate_by_state_top5"].items():
        lines.append(f"- **{k}**: {v*100:.2f}%\n")
    lines.append("\n## Bottom 5 estados (menor default rate)\n")
    for k, v in stats["default_rate_by_state_bottom5"].items():
        lines.append(f"- **{k}**: {v*100:.2f}%\n")

    lines.append("\n## Figuras generadas\n")
    for f in figures:
        lines.append(f"- `{f}`\n")

    with open(f"{RESULTS_DIR}/eda_report.md", "w") as f:
        f.writelines(lines)

    print(f"\nFiguras guardadas: {len(figures)}")
    for f in figures:
        print(f"  {f}")
    print(f"\nStats: {RESULTS_DIR}/eda_stats.json")
    print(f"Reporte: {RESULTS_DIR}/eda_report.md")


if __name__ == "__main__":
    main()
