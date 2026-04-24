# EDA inicial — Lending Club
Muestra estratificada: **200,000 filas × 49 columnas**.
Tasa base de default: **19.96%**.

## Default rate por grade
| Grade | Default rate |
|---|---|
| A | 5.92% |
| B | 13.36% |
| C | 22.49% |
| D | 30.29% |
| E | 38.01% |
| F | 46.75% |
| G | 50.00% |

## Pricing vs riesgo por grade
| Grade | Tasa interés media | Default rate | N |
|---|---|---|---|
| A | 7.12% | 5.92% | 34,984 |
| B | 10.68% | 13.36% | 58,315 |
| C | 14.02% | 22.49% | 56,522 |
| D | 17.71% | 30.29% | 29,938 |
| E | 21.13% | 38.01% | 13,956 |
| F | 24.95% | 46.75% | 4,937 |
| G | 27.83% | 50.00% | 1,348 |

## Top 5 estados con mayor default rate
- **NE**: 26.68%
- **MS**: 25.65%
- **NV**: 23.81%
- **AR**: 23.76%
- **AL**: 23.47%

## Bottom 5 estados (menor default rate)
- **NH**: 15.43%
- **WY**: 14.96%
- **OR**: 14.92%
- **ME**: 14.63%
- **DC**: 14.17%

## Figuras generadas
- `paper/figures/eda_nulls.png`
- `paper/figures/eda_default_by_grade.png`
- `paper/figures/eda_default_by_subgrade.png`
- `paper/figures/eda_default_by_purpose.png`
- `paper/figures/eda_default_by_state.png`
- `paper/figures/eda_continuous_by_default.png`
- `paper/figures/eda_temporal.png`
- `paper/figures/eda_pricing_vs_default_by_grade.png`
- `paper/figures/eda_pricing_risk_scatter.png`
