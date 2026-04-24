# Revisión de Literatura — Borrador

> Borrador automatizado de revisión de literatura, generado por subagente de investigación.
> **Uso:** insumo para la sección de *Marco Teórico* y *Revisión de Literatura* del paper final.
> Verificar DOIs y revisar citas críticas manualmente antes de la entrega.

---

## Pilar 1: Fundamentos teóricos — fallas de mercado crediticio

**Stiglitz, J. & Weiss, A. (1981)** "Credit Rationing in Markets with Imperfect Information" — *American Economic Review*, 71(3), pp. 393-410.
- URL: https://www.jstor.org/stable/1802787
- Resumen: Modelo seminal donde la tasa de interés actúa como mecanismo de selección adversa; los bancos racionan crédito en lugar de subir tasas porque tasas más altas empeoran la calidad del pool de deudores.
- Método: Teórico (modelo de equilibrio con información asimétrica).
- Relevancia: Base teórica para justificar por qué el *pricing* puede divergir del riesgo real; sustenta la hipótesis de que Lending Club podría no internalizar perfectamente el riesgo idiosincrático.
- Citabilidad: ALTA.

**Akerlof, G. (1970)** "The Market for 'Lemons': Quality Uncertainty and the Market Mechanism" — *Quarterly Journal of Economics*, 84(3), pp. 488-500.
- DOI: 10.2307/1879431
- Resumen: Demuestra cómo la información asimétrica genera selección adversa y puede colapsar mercados.
- Relevancia: Cita obligatoria para enmarcar por qué existen grades/tasas como señales; en P2P la asimetría es aún mayor porque el prestamista es retail.
- Citabilidad: ALTA.

## Pilar 2: ML aplicado a scoring crediticio

**Khandani, A., Kim, A. & Lo, A. (2010)** "Consumer Credit-Risk Models via Machine-Learning Algorithms" — *Journal of Banking & Finance*, 34(11), pp. 2767-2787.
- DOI: 10.1016/j.jbankfin.2010.06.001
- Resumen: Usan árboles de decisión (CART) sobre datos transaccionales de un banco comercial; superan modelos logit tradicionales en predicción de default, con ahorros del 6-25% en pérdidas.
- Método: ML (árboles) vs. logit.
- Datos: EE.UU., 2005-2009, ~150.000 clientes.
- Relevancia: Antecedente canónico para comparar XGBoost vs. logit; justifica metodológicamente la superioridad predictiva del ML.
- Citabilidad: ALTA.

## Pilar 3: Fairness algorítmica

**Barocas, S. & Selbst, A. (2016)** "Big Data's Disparate Impact" — *California Law Review*, 104(3), pp. 671-732.
- DOI: 10.15779/Z38BG31
- Resumen: Documenta cómo algoritmos entrenados sobre datos históricos pueden producir discriminación indirecta aun sin usar variables protegidas; taxonomía de mecanismos de sesgo.
- Relevancia: Fundamento conceptual para el *fairness audit sin atributos protegidos observables* mediante proxies.
- Citabilidad: ALTA.

**Chen, J., Kallus, N., Mao, X., Svacha, G. & Udell, M. (2019)** "Fairness Under Unawareness: Assessing Disparity When Protected Class Is Unobserved" — *FAccT 2019*, pp. 339-348.
- DOI: 10.1145/3287560.3287594
- Resumen: Método para estimar disparidad cuando la variable protegida no se observa; usa BISG (Bayesian Improved Surname Geocoding) como proxy.
- Datos: Aplicación a datos de crédito HMDA.
- Relevancia: **CRÍTICO** — operacionaliza técnicamente lo que vamos a hacer con proxies. Puente metodológico directo.
- Citabilidad: ALTA.

## Pilar 4: Lending Club / P2P lending

**Hertzberg, A., Liberman, A. & Paravisini, D. (2018)** "Screening on Loan Terms: Evidence from Maturity Choice in Consumer Credit" — *Review of Financial Studies*, 31(9), pp. 3532-3567.
- DOI: 10.1093/rfs/hhy024
- Resumen: Usa datos de Lending Club; muestra que la elección del plazo por el prestatario revela información privada sobre su riesgo, evidencia de selección adversa residual.
- Datos: Lending Club, 2012-2014, ~100.000 préstamos.
- Relevancia: Prueba empírica de que los grades/tasas de LC NO capturan toda la info de riesgo — justifica directamente nuestra pregunta de *pricing efficiency*.
- Citabilidad: ALTA. **CITA OBLIGATORIA.**

**Bartlett, R., Morse, A., Stanton, R. & Wallace, N. (2022)** "Consumer-Lending Discrimination in the FinTech Era" — *Journal of Financial Economics*, 143(1), pp. 30-56.
- DOI: 10.1016/j.jfineco.2021.05.047
- Resumen: Documentan que algoritmos fintech de crédito hipotecario cobran tasas más altas a minorías latinas/afroamericanas aun controlando por riesgo; discriminación reducida ~40% vs. face-to-face pero persistente.
- Datos: EE.UU., 2008-2015, ~7M préstamos hipotecarios (HMDA).
- Relevancia: Paper más cercano a nuestro ángulo de *fairness + pricing*; **CITA OBLIGATORIA**.
- Citabilidad: ALTA.

## Pilar 5: SHAP / interpretabilidad

**Lundberg, S. & Lee, S.-I. (2017)** "A Unified Approach to Interpreting Model Predictions" — *NeurIPS 2017*, pp. 4765-4774.
- URL: https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767
- Resumen: Introduce SHAP values basados en teoría de juegos (Shapley); unifica métodos de interpretabilidad local.
- Relevancia: Cita metodológica indispensable para justificar SHAP en el *audit*.
- Citabilidad: ALTA.

## Pilar 6: ML-econometría

**Mullainathan, S. & Spiess, J. (2017)** "Machine Learning: An Applied Econometric Approach" — *Journal of Economic Perspectives*, 31(2), pp. 87-106.
- DOI: 10.1257/jep.31.2.87
- Resumen: Distinguen problemas de predicción (ŷ) vs. inferencia causal (β̂); argumentan cuándo ML aporta valor en economía.
- Relevancia: Justificación epistemológica para usar XGBoost en un paper de economía.
- Citabilidad: ALTA.

---

## Veredicto de originalidad

**NO** existe un paper publicado que combine exactamente: Lending Club + pricing efficiency (tasa observada vs. riesgo predicho ML) + fairness audit con proxies socioeconómicos/geográficos + XGBoost + SHAP.

**Contribución marginal defendible:**

1. Medición de *mispricing residual* en P2P no corporativo con un estimador ML state-of-the-art (XGBoost).
2. Audit de fairness cuando el regulador/investigador NO observa la variable protegida — condición realista en Colombia y mercados emergentes.
3. Descomposición SHAP de las fuentes de disparidad, distinguiendo proxies legítimos (ingreso) de sospechosos (geografía con correlación racial).

## Riesgos metodológicos a declarar en el paper

- **Cita obligatoria:** Bartlett et al. (2022) y Hertzberg et al. (2018). No citarlas sería fatal en defensa.
- **Debate abierto:** tensión entre *fairness through unawareness* (no usar variable sensible) vs. *disparate impact* (Barocas-Selbst). Nuestro paper contribuye mostrando que la unawareness en P2P no es suficiente.
- **SHAP críticas:** Kumar et al. (2020, ICML) señalan problemas de interpretación causal — reconocerlo explícitamente.
- **Cierre de Lending Club:** LC cerró su plataforma P2P retail en 2020; panel truncado en ese año. Declararlo.

## Citas core obligatorias

1. **Bartlett, Morse, Stanton & Wallace (2022, JFE)** — benchmark empírico directo.
2. **Chen, Kallus, Mao, Svacha & Udell (2019, FAccT)** — puente metodológico para proxies.
3. **Stiglitz & Weiss (1981, AER)** — ancla teórica que legitima el trabajo como economía, no solo ML.
