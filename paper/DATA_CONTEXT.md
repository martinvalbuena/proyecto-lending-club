# Contexto de los datos — Lending Club Loan Data

Material de referencia para la Sección 2 del paper ("Descripción de los datos") y para defensa académica del proyecto.

---

## Origen institucional

**Lending Club** fue una plataforma de *peer-to-peer lending* (P2P) fundada en 2006 en San Francisco por Renaud Laplanche. Su modelo de negocio era conectar directamente a consumidores estadounidenses que solicitaban préstamos personales no garantizados con inversionistas retail e institucionales que compraban fracciones de esos préstamos ($25 mínimo), eliminando al banco tradicional como intermediario. En diciembre de 2014 salió a bolsa (NYSE: LC) en la mayor IPO tecnológica estadounidense de ese año.

Tres fuerzas convirtieron a Lending Club en uno de los datasets más utilizados de la literatura empírica de crédito al consumo:

1. **Obligación regulatoria.** Desde 2008 la SEC clasificó los préstamos de Lending Club como *securities*. Esto obligó a la empresa a emitir *prospectos* detallados y mantener transparencia granular sobre cada préstamo emitido.
2. **Estrategia comercial.** Para atraer capital institucional, Lending Club publicaba activamente el histórico completo de préstamos emitidos en su sitio web, permitiendo a inversionistas construir sus propios modelos de riesgo.
3. **Accesibilidad académica.** El resultado fue un benchmark público estándar utilizado en más de cien papers revisados por pares, incluyendo los citados en este proyecto (Hertzberg, Liberman & Paravisini 2018, RFS; Bartlett, Morse, Stanton & Wallace 2022, JFE usa un dataset relacionado de HMDA).

## Cierre y procedencia de la copia utilizada

En mayo de 2016 Lending Club enfrentó una crisis reputacional cuando se descubrió que su CEO había vendido $22M en préstamos a un cliente institucional con términos alterados sin autorización. La confianza del mercado no se recuperó. En octubre de 2020 la empresa cerró definitivamente su plataforma P2P retail, pivotando a banca tradicional mediante la adquisición de Radius Bank. Al cerrar la plataforma, el histórico público fue retirado del sitio web.

La copia utilizada en este proyecto proviene del mirror público mantenido en Kaggle por el usuario `wordsforthewise` (dataset: `wordsforthewise/lending-club`), que preservó los archivos originales antes del cierre. Cubre los **2.26 millones de préstamos emitidos entre junio de 2007 y diciembre de 2018**.

## Unidad de observación

Cada fila del dataset representa **un préstamo emitido** por Lending Club — no un individuo, no una aplicación. Un mismo prestatario podría aparecer más de una vez si tomó múltiples préstamos (aunque Lending Club limitaba a dos préstamos simultáneos por prestatario).

El prestatario típico:
- Reside en Estados Unidos (Lending Club nunca operó fuera).
- Solicita un préstamo personal no garantizado entre $500 y $40,000.
- Escoge un plazo de 36 o 60 meses.
- Usa el préstamo principalmente para consolidación de deuda de tarjetas de crédito (propósito dominante: ~58% de los préstamos).

## Proceso de generación de datos

Los valores de cada observación provienen de tres fuentes distintas, con distinto grado de confiabilidad:

1. **Autorreporte del prestatario.** Campos como `annual_inc` (ingreso), `emp_title` (título laboral), `emp_length` (antigüedad), `home_ownership` y `purpose` fueron declarados por el solicitante al llenar la aplicación online. Lending Club verificaba el ingreso solo en un subconjunto de casos (ver `verification_status`).

2. **Reporte de burós de crédito.** Variables como `fico_range_low/high`, `dti`, `delinq_2yrs`, `open_acc`, `revol_bal`, `revol_util`, `pub_rec`, y el resto del bloque crediticio provienen de una consulta a un buró (TransUnion o Experian) al momento de la aplicación. Estos son verificados por tercero y se consideran de alta confiabilidad.

3. **Asignación interna de Lending Club.** `grade`, `sub_grade` e `int_rate` son outputs del modelo de pricing de Lending Club — no provienen de fuente externa. Son el objeto de auditoría central de este proyecto.

4. **Registro longitudinal post-origen.** Variables como `total_pymnt`, `recoveries`, `last_pymnt_d` y `last_fico_range_*` se actualizan mensualmente por Lending Club según el comportamiento de pago del prestatario después del desembolso. No pueden usarse como features predictivos al origen sin incurrir en *data leakage*.

## Sesgos de selección a declarar

Toda inferencia del proyecto debe interpretarse **condicional** a los siguientes sesgos:

- **Autoselección del prestatario.** Los usuarios de Lending Club no son representativos de la población general. Son usuarios típicamente *tech-savvy*, con algún historial crediticio previo, buscando refinanciar deuda existente. La literatura (Morse 2015, JFE) documenta que los usuarios P2P tienen en promedio FICO mayor al mediano nacional y son *early adopters* digitales.

- **Selección del underwriting.** El dataset solo incluye préstamos **aprobados**. El archivo complementario `rejected_*.csv.gz` contiene ~27 millones de aplicaciones rechazadas con variables limitadas (solo FICO, DTI, monto, propósito, estado, zip). El modelo predictivo de este proyecto se interpreta como: *probabilidad de default condicional a haber sido aprobado por LC*.

- **Cambios temporales en el underwriting.** Las reglas internas de asignación de grade evolucionaron entre 2007 y 2018. Un grade "C" de 2012 no es estrictamente equivalente a un grade "C" de 2017. Por esta razón el análisis se restringe a la ventana **2012-2017** (seis vintages con underwriting razonablemente estable, eliminando también el ruido de vintages tempranos de bajo volumen y el *right-censoring* de 2018).

- **Ausencia de variable racial/étnica.** Lending Club no recolectaba raza ni origen étnico, amparándose en la Equal Credit Opportunity Act (ECOA) que permite — pero no obliga — a prestamistas de crédito al consumo no hipotecario a no recolectar estas variables. Esta ausencia es **precisamente la condición motivadora** del fairness audit por proxies propuesto en la Hipótesis 2 del proyecto (ver Chen, Kallus, Mao, Svacha & Udell 2019, FAccT).

- **Censura derecha de préstamos recientes.** Los préstamos emitidos cerca del corte del dataset (Q4-2018) a plazo de 36 o 60 meses aún no habían madurado completamente. Sus tasas de default observadas son **subestimaciones** de la tasa terminal. La ventana 2012-2017 mitiga este problema garantizando que todos los préstamos tenían al menos un año de observación post-término nominal al momento del corte.

## Relación con la literatura

Dos papers canónicos de la lit review usan este dataset o uno relacionado:

- **Hertzberg, Liberman & Paravisini (2018, Review of Financial Studies).** Usan Lending Club 2012-2014 para mostrar que la elección del plazo por parte del prestatario (36 vs 60 meses) revela información privada sobre riesgo no capturada en el grade — evidencia directa de selección adversa residual.

- **Bartlett, Morse, Stanton & Wallace (2022, Journal of Financial Economics).** Usan HMDA (datos hipotecarios con variable racial obligatoria por ley) para documentar discriminación algorítmica en *fintech lending*. Sirve como benchmark empírico directo para nuestra Hipótesis 2, aunque en un segmento de crédito distinto.

El hueco que ataca este proyecto: *fairness audit* en crédito al consumo **no hipotecario** — donde la variable sensible no es observable — combinado con análisis de eficiencia del pricing mediante machine learning. No existe (al momento de esta revisión de literatura) un paper publicado que combine exactamente estas cuatro piezas en Lending Club.

---

## Tratamiento de outliers y argumento de elección de modelo

Durante el preprocessing se detectaron valores extremos en la cola derecha de cinco variables continuas. Esta sección documenta el tratamiento aplicado y su relación con la elección metodológica de modelar con **XGBoost como modelo principal**.

### Outliers detectados

| Variable | Valor máximo crudo | Interpretación del extremo |
|---|---:|---|
| `loan_to_income` | 35,000× | Razón préstamo/ingreso de 35,000 implica `annual_inc ≈ $1`. Error de captura o ingreso declarado en centavos |
| `dti` | 999% | Placeholder de Lending Club cuando el algoritmo no podía computar DTI (ingreso cero, deuda indeterminada) |
| `revol_util` | 366% | Técnicamente posible bajo intereses moratorios, pero extremo |
| `annual_inc` | >$10M | Ingresos plausibles pero dominantes en la cola |
| `revol_bal` | >$1M | Saldo revolvente plausible pero extremo |

La prevalencia de estos valores es baja (< 1% de la muestra en cada variable), pero su impacto sobre modelos lineales es desproporcionado.

### Tratamiento aplicado

Dos intervenciones, ambas conservadoras:

1. **Filtrado de filas con `annual_inc ≤ 0`** (29 filas, 0.014% de la muestra). Estas filas casi con seguridad son errores de captura — ningún prestatario con ingreso anual cero es aprobado por el underwriting de Lending Club. Se eliminan del dataset procesado.

2. **Winsorización al percentil 99 de la cola derecha** en las cinco variables listadas. El umbral se calcula exclusivamente sobre el conjunto de entrenamiento y se aplica a validación y test, preservando la disciplina de no-leakage. La winsorización es una práctica estándar en economía financiera empírica (Bartlett, Morse, Stanton & Wallace 2022, *Journal of Financial Economics*, entre otros) y se prefiere sobre la eliminación total porque conserva la observación mientras limita su influencia desproporcionada en la función objetivo.

Los umbrales P99 finales, calculados en train:

| Variable | Umbral P99 |
|---|---:|
| `annual_inc` | $250,000 |
| `loan_to_income` | 0.50× |
| `dti` | 38.20% |
| `revol_util` | 98.20% |
| `revol_bal` | $94,337 |

### Por qué esto importa para la elección de modelo

La sensibilidad a outliers difiere fundamentalmente entre las dos familias de modelos que usamos en el proyecto:

**Regresión logística (baseline).** La función de pérdida log-loss es $\sum_i -y_i \log \hat{p}_i - (1-y_i) \log(1-\hat{p}_i)$, donde $\hat{p}_i = \sigma(\beta^\top x_i)$. Un valor extremo en $x_i$ empuja $\beta^\top x_i$ hacia el extremo correspondiente de la sigmoide, saturando la predicción y generando gradientes desproporcionados durante la optimización. En la práctica esto significa que **una sola observación con `dti = 999` puede dominar el estimador del coeficiente de `dti`**, distorsionando la inferencia para todas las demás observaciones. Sin tratamiento de outliers, la regresión logística no es robusta.

**XGBoost (modelo principal).** Los árboles de decisión (y su extensión a gradient boosting) particionan el espacio de features con reglas de la forma $x_j \leq c$. La decisión de partición depende del **orden** de los valores de $x_j$, no de sus magnitudes absolutas. Un valor extremo en la cola derecha simplemente cae en la partición "valor alto"; su valor específico (100, 1000, o 999,999) es irrelevante para la estructura del árbol. XGBoost es, por construcción, invariante a transformaciones monotónicas y robusto a outliers.

### Implicación metodológica

La robustez a outliers es uno de varios argumentos a favor de usar XGBoost como modelo principal en lugar de una regresión logística tradicional:

1. **Robustez a outliers** (discutido arriba).
2. **Capacidad de modelar interacciones no-lineales** sin especificación manual de términos de interacción (el EDA mostró separabilidad modesta univariada entre default y no-default; la señal probable vive en combinaciones de variables).
3. **Manejo automático de colinealidad** entre features correlacionados (ej. FICO y revol_util capturan ambos aspectos de disciplina crediticia).
4. **Performance consistente** en benchmarks de riesgo crediticio (Khandani, Kim & Lo 2010, *Journal of Banking & Finance*).

Aplicamos la winsorización a los features de **ambos** modelos para garantizar que la comparación sea metodológicamente justa (controlamos por el tratamiento de datos, no por diferencias en qué versión de los datos ve cada modelo). El argumento de robustez relativa se sostiene **a pesar** de que ambos modelos ven los mismos datos: si no hubiéramos winsorizado, Logit se habría degradado mientras XGBoost habría quedado prácticamente inalterado.

Esta decisión se discute en la Sección 3 (Construcción de Modelos) del paper y se refuerza en la Sección 4 cuando se compare el desempeño de ambos modelos sobre el conjunto de test.

---

## Diccionario de variables

Las variables se agrupan por origen (autorreporte, buró, asignación interna, post-origen) y por su rol en el proyecto (target, feature predictivo, feature auxiliar, post-origen descriptivo).

### Target y pricing

| Variable | Definición | Fuente | Rol en el modelo |
|---|---|---|---|
| `loan_status` | Estado final del préstamo. Nueve categorías posibles: Fully Paid, Charged Off, Current, Default, In Grace Period, Late (16-30), Late (31-120), Does not meet the credit policy. Status:Fully Paid, Does not meet the credit policy. Status:Charged Off | LC longitudinal | Construcción del target binario `default` |
| `loan_amnt` | Monto solicitado por el prestatario, en USD. Rango típico: $500 – $40,000 | Autorreporte | Feature predictivo |
| `int_rate` | Tasa de interés anual asignada por LC, en porcentaje. Rango típico: 5.3% – 30.9% | Asignación LC | **No** es feature (sería circular). Usado como benchmark de pricing en Sección 5 |
| `grade` | Grado de riesgo de LC (A = mejor, G = peor). Asignado por algoritmo interno de underwriting | Asignación LC | **No** es feature (sería leakage del pricing). Usado como baseline en Sección 4 |
| `sub_grade` | Subdivisión del grade en 5 niveles (A1 = mejor dentro de A, A5 = peor). 35 niveles totales (A1-G5) | Asignación LC | **No** es feature. Usado como baseline granular |
| `term` | Plazo del préstamo: 36 o 60 meses | Elección del prestatario | Feature predictivo (limpiado a `term_months`) |
| `installment` | Pago mensual calculado por amortización estándar dados `loan_amnt`, `int_rate`, `term` | Derivado | Excluido (derivable de otros) |

### Metadatos del préstamo

| Variable | Definición | Fuente |
|---|---|---|
| `issue_d` | Mes y año en que se desembolsó el préstamo | LC |
| `purpose` | Propósito del préstamo declarado por el prestatario. 12 categorías: debt_consolidation, credit_card, home_improvement, major_purchase, medical, car, small_business, vacation, wedding, moving, house, other | Autorreporte |
| `title` | Título del préstamo escrito libremente. En la mayoría de casos repite `purpose` con capitalización distinta | Autorreporte |
| `application_type` | "Individual" o "Joint App". Joint disponible solo a partir de 2017 | LC |
| `initial_list_status` | "W" = *whole loan* (vendido completo a un inversionista institucional). "F" = *fractional* (fraccionado entre retail) | LC |
| `disbursement_method` | "Cash" (depósito directo al prestatario) o "DirectPay" (LC paga directamente a acreedores en casos de consolidación) | LC |

### Demografía y empleo (autorreporte)

| Variable | Definición |
|---|---|
| `emp_title` | Título del empleo, texto libre. Cardinalidad muy alta (~50K valores únicos). Ejemplo: "Teacher", "Software Engineer", "Nurse". Se descarta del modelo por ruido. |
| `emp_length` | Antigüedad laboral en tramos categóricos: `<1 year`, `1 year`, `2 years`, …, `10+ years`. Se codifica como ordinal numérico |
| `home_ownership` | Estatus de vivienda. Niveles principales: RENT, OWN, MORTGAGE. Raros: ANY, NONE, OTHER (agrupados) |
| `annual_inc` | Ingreso anual autorreportado, en USD. Distribución muy sesgada (cola derecha larga, valores atípicos hasta $10M). Se transforma con `log1p` para modelado |
| `verification_status` | Grado de verificación del ingreso: `Verified` (verificado con documentación), `Source Verified` (fuente validada), `Not Verified` |
| `addr_state` | Estado de residencia, código postal de 2 letras (50 estados + DC). Usado para el análisis de heterogeneidad geográfica y como proxy de fairness. En el modelo se agrega a 4 regiones del U.S. Census |
| `zip_code` | Primeros 3 dígitos del ZIP, enmascarado como "123xx" por privacidad |

### Historial crediticio al origen (reporte de buró)

Fuente de alta confiabilidad — verificado por tercero (TransUnion o Experian al momento de la aplicación).

| Variable | Definición |
|---|---|
| `dti` | *Debt-to-income ratio*: pagos mensuales de deuda (excluyendo el nuevo préstamo de LC) divididos por ingreso bruto mensual, expresado como porcentaje |
| `delinq_2yrs` | Número de atrasos de 30+ días reportados en los últimos 24 meses |
| `earliest_cr_line` | Fecha de la línea de crédito más antigua en el reporte del buró. Proxy de antigüedad del historial crediticio |
| `fico_range_low`, `fico_range_high` | Rango del FICO score al origen. FICO va de 300 a 850 (más alto = mejor crédito). LC reporta el rango (típicamente 4-5 puntos de ancho) en vez del valor puntual |
| `inq_last_6mths` | Número de consultas duras (*hard inquiries*) al reporte crediticio en los últimos 6 meses. Cada aplicación nueva de crédito genera una consulta dura |
| `open_acc` | Número de cuentas de crédito abiertas al momento del origen |
| `pub_rec` | Número de registros públicos negativos (bancarrotas, embargos, juicios civiles) |
| `revol_bal` | Saldo revolvente total, principalmente deuda de tarjetas de crédito, en USD |
| `revol_util` | *Revolving utilization*: saldo revolvente usado dividido por límite disponible total, como porcentaje. Métrica clave del *credit scoring* moderno |
| `total_acc` | Número total de cuentas de crédito en el historial (abiertas + cerradas) |
| `mort_acc` | Número de cuentas hipotecarias. Proxy de estabilidad financiera (propietarios suelen tener menor riesgo) |
| `pub_rec_bankruptcies` | Subset específico de `pub_rec`: solo bancarrotas personales (Capítulo 7 o 13 en EE.UU.) |
| `tax_liens` | Número de embargos por deudas fiscales |
| `acc_now_delinq` | Número de cuentas que están **actualmente** en atraso al momento del origen (señal de estrés financiero inmediato) |
| `chargeoff_within_12_mths` | Número de préstamos declarados incobrables (*charge-off*) por otros acreedores en los últimos 12 meses |
| `collections_12_mths_ex_med` | Número de cuentas enviadas a agencia de cobranza en los últimos 12 meses, excluyendo deuda médica (la deuda médica se trata distinto por regulación FCRA) |

### Variables post-origen — no-features

Estas variables se actualizan después del desembolso del préstamo. Su uso como features del modelo constituiría *data leakage* (el modelo "sabe el futuro"). Se conservan en el dataset procesado en un archivo separado (`df_meta_*.parquet`) para análisis descriptivo, validación y el cálculo de retornos realizados en la Sección 5.

| Variable | Definición |
|---|---|
| `total_pymnt` | Total de pagos recibidos al momento del corte del dataset, en USD |
| `total_rec_prncp` | Porción de `total_pymnt` correspondiente a principal |
| `total_rec_int` | Porción correspondiente a interés |
| `recoveries` | Dinero recuperado después de que LC declaró *charge-off* (via agencia de cobranza) |
| `last_pymnt_d` | Fecha del último pago recibido |
| `last_fico_range_low`, `last_fico_range_high` | FICO en la última actualización del buró (post-desembolso) |

---

*Versión: 2026-04-24. Autor: Martín Valbuena.*
