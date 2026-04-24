# Eficiencia del Pricing del Riesgo Crediticio en Mercados P2P

**Un Análisis de Machine Learning con Auditoría de Fairness por Proxies en Lending Club**

Proyecto académico — Universidad de Los Andes, curso de Machine Learning para Economía, 2026-1.
Autor: Martín Valbuena.

---

## Pregunta de investigación

¿En qué medida las tasas de interés asignadas por Lending Club reflejan el riesgo de *default* predicho por modelos de machine learning (XGBoost, con baselines Logit y *grades* observados), y existen disparidades sistemáticas en el *mispricing* entre subgrupos geográficos y socioeconómicos que puedan indicar fallas de mercado o discriminación indirecta?

## Hipótesis

- **H1:** El pricing observado de Lending Club tiene ineficiencias — el sistema de *grades* simplifica la heterogeneidad de riesgo y modelos ML identifican mispricing residual.
- **H2:** Las disparidades de mispricing se distribuyen de forma no uniforme entre subgrupos identificados por proxies (estado, tramo de ingreso, ocupación), sugiriendo discriminación indirecta o selección geográfica.
- **H3:** Un *fair re-pricing* basado en predicciones ML redistribuye las tasas con implicaciones sobre acceso al crédito.

## Marco teórico (referencias principales)

- **Stiglitz & Weiss (1981, AER)** — *Credit rationing with imperfect information*
- **Akerlof (1970, QJE)** — *The market for lemons*
- **Bartlett, Morse, Stanton & Wallace (2022, JFE)** — *Consumer-lending discrimination in the FinTech era*
- **Hertzberg, Liberman & Paravisini (2018, RFS)** — *Screening on loan terms: evidence from Lending Club*
- **Chen, Kallus, Mao, Svacha & Udell (2019, FAccT)** — *Fairness under unawareness*
- **Mullainathan & Spiess (2017, JEP)** — *Machine learning: an applied econometric approach*
- **Lundberg & Lee (2017, NeurIPS)** — *A unified approach to interpreting model predictions (SHAP)*
- **Barocas & Selbst (2016, California Law Review)** — *Big data's disparate impact*

## Datos

**Lending Club Loan Data** (2007-2018). Dataset público de préstamos P2P. Submuestreo estratificado a ~200K filas para iteración rápida.

## Metodología

1. **Preprocessing**: imputación, encoding de categóricas, filtrado por `loan_status` definitivo, train/val/test estratificado 70/15/15.
2. **Modelos**: XGBoost (principal, con mini grid search + calibración Platt). Baselines: Regresión Logística con interacciones; *grades* observados de Lending Club.
3. **Interpretabilidad**: SHAP global y local.
4. **Heterogeneidad**: análisis de drivers por subgrupo (estado, tramo de ingreso, home ownership).
5. **Pricing comparison**: tasa observada vs. tasa *fair-predicted* derivada de probabilidad de default calibrada.
6. **Fairness audit**: equalized odds y predictive parity por proxies sociodemográficos.

## Estructura del repositorio

```
.
├── data/
│   ├── raw/            # Dataset original (no versionado)
│   └── processed/      # Splits train/val/test (no versionados)
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_models.ipynb
│   ├── 04_heterogeneity_shap.ipynb
│   └── 05_pricing_fairness.ipynb
├── src/                # Módulos reutilizables
├── paper/              # Manuscrito LaTeX
│   ├── main.tex
│   ├── references.bib
│   └── figures/
├── slides/             # Presentación Beamer
│   └── slides.tex
├── results/            # Tablas y figuras exportadas
├── requirements.txt
└── README.md
```

## Reproducibilidad

```bash
# 1. Clonar repo
git clone https://github.com/mvalbuenal/lending-club-pricing-fairness.git
cd lending-club-pricing-fairness

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Descargar dataset (ver instrucciones en notebooks/01_eda.ipynb)

# 5. Correr notebooks en orden (01 → 05)
jupyter notebook
```

## Licencia

Proyecto académico. Contenido con fines educativos y de investigación.
