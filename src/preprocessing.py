"""
Pipeline de preprocessing — Lending Club.

Entrada:  data/processed/{train,val,test}.parquet (salida de src/build_dataset.py)
Salida:   data/processed/X_{train,val,test}.parquet  (features numéricos listos para modelo)
          data/processed/y_{train,val,test}.npy      (target binario)
          data/processed/meta_{train,val,test}.parquet  (cols no-feature preservadas:
                                                        int_rate, grade, sub_grade,
                                                        addr_state, issue_d, loan_status,
                                                        y post-origen para retornos)
          data/processed/preprocessing_metadata.json

Decisiones (documentadas en paper/DATA_CONTEXT.md y discusión EDA):
  - Filtro temporal: issue_year in [2012, 2017]
  - addr_state → 4 regiones U.S. Census
  - Features derivadas: fico_avg, credit_history_yrs, loan_to_income, log_annual_inc, term_months
  - Imputación de nulos: mediana para continuas, 0 para mort_acc, + dummy de missingness
  - Imputación se fittea en TRAIN y aplica a val/test (evita leakage)
  - Encoding: one-hot para purpose, home_ownership, verification_status, application_type,
    initial_list_status, disbursement_method, region
  - No-features en el modelo: int_rate, grade, sub_grade (preservados en meta_ para analisis)
  - Variables post-origen: preservadas en meta_ para cálculo de retornos en Sección 5
"""
import os
import json
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
PROCESSED_DIR = "data/processed"
YEAR_MIN, YEAR_MAX = 2012, 2017

# Mapeo de estado a región (U.S. Census Bureau)
REGION_MAP = {
    # Northeast
    **{s: "Northeast" for s in ["CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"]},
    # Midwest
    **{s: "Midwest" for s in ["IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE",
                               "ND", "OH", "SD", "WI"]},
    # South (incluye DC por convenciones Census)
    **{s: "South" for s in ["AL", "AR", "DE", "DC", "FL", "GA", "KY", "LA",
                             "MD", "MS", "NC", "OK", "SC", "TN", "TX", "VA", "WV"]},
    # West
    **{s: "West" for s in ["AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NV",
                            "NM", "OR", "UT", "WA", "WY"]},
}

# Cols preservadas en meta_ (no entran al modelo pero se usan downstream)
META_COLS = [
    "int_rate", "grade", "sub_grade",
    "addr_state", "region", "issue_d", "issue_year",
    "loan_status",
    # Post-origen para retornos y validación
    "total_pymnt", "total_rec_prncp", "total_rec_int", "recoveries",
    "last_pymnt_d", "last_fico_range_low", "last_fico_range_high",
]

# Cols que se droppean completamente (no son feature ni van al meta)
DROP_COLS = [
    "emp_title",        # Texto libre, alta cardinalidad (~50K únicos)
    "title",            # Redundante con purpose
    "zip_code",         # Redundante con addr_state, alta cardinalidad
    "installment",      # Derivable de loan_amnt, int_rate, term
    "earliest_cr_line", # Reemplazado por credit_history_yrs
    "fico_range_low",   # Reemplazado por fico_avg
    "fico_range_high",  # Reemplazado por fico_avg
]

# Cols categóricas para one-hot
OH_COLS = [
    "purpose", "home_ownership", "verification_status",
    "application_type", "initial_list_status", "disbursement_method",
    "region",
]

# Cols continuas que necesitan imputación con mediana
IMPUTE_MEDIAN_COLS = [
    "revol_util", "dti", "pub_rec_bankruptcies",
]

# Cols con imputación + dummy de missingness
IMPUTE_WITH_DUMMY_COLS = [
    ("emp_length_num", "median"),
    ("mort_acc", "zero"),
]

# Cols a winsorizar al percentil 99 (outliers extremos en cola derecha).
# Ver DATA_CONTEXT.md sección "Tratamiento de outliers".
WINSORIZE_COLS = ["annual_inc", "loan_to_income", "dti", "revol_util", "revol_bal"]
WINSORIZE_PCT = 0.99


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
def parse_emp_length(s):
    """'< 1 year' -> 0, '1 year' -> 1, '10+ years' -> 10, NaN -> NaN."""
    if pd.isna(s):
        return np.nan
    s = str(s).strip()
    if "<" in s:
        return 0
    if "+" in s:
        return 10
    try:
        return int(s.split()[0])
    except (ValueError, IndexError):
        return np.nan


def parse_percent_string(s):
    """'13.99%' -> 13.99. Si ya es float, lo devuelve."""
    if pd.isna(s):
        return np.nan
    if isinstance(s, (int, float)):
        return float(s)
    return float(str(s).rstrip("%").strip())


def parse_term(s):
    """' 36 months' -> 36."""
    if pd.isna(s):
        return np.nan
    if isinstance(s, (int, float)):
        return float(s)
    return int(str(s).strip().split()[0])


def clean_home_ownership(s):
    """Agrupa niveles raros."""
    if pd.isna(s):
        return "OTHER"
    s = str(s).strip().upper()
    if s in {"RENT", "OWN", "MORTGAGE"}:
        return s
    return "OTHER"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def clean_raw(df):
    """Limpieza común a train/val/test: parseos, filtros, feature engineering."""
    df = df.copy()

    # Parseo de fechas
    df["issue_d"] = pd.to_datetime(df["issue_d"], format="%b-%Y", errors="coerce")
    df["issue_year"] = df["issue_d"].dt.year
    df["earliest_cr_line"] = pd.to_datetime(df["earliest_cr_line"], format="%b-%Y", errors="coerce")
    df["last_pymnt_d"] = pd.to_datetime(df["last_pymnt_d"], format="%b-%Y", errors="coerce")

    # Filtro temporal
    df = df[df["issue_year"].between(YEAR_MIN, YEAR_MAX)].copy()

    # Filtro de calidad de datos: annual_inc > 0
    # (valores en 0 producen loan_to_income infinito y son casi seguro errores
    # de captura. ~0.01% de la muestra.)
    n_before = len(df)
    df = df[df["annual_inc"] > 0].copy()
    n_zero_inc = n_before - len(df)
    if n_zero_inc > 0:
        print(f"    - Filtradas {n_zero_inc} filas con annual_inc <= 0")

    # Parseo de strings numéricos
    df["int_rate"] = df["int_rate"].apply(parse_percent_string)
    df["revol_util"] = df["revol_util"].apply(parse_percent_string)
    df["term_months"] = df["term"].apply(parse_term)
    df["emp_length_num"] = df["emp_length"].apply(parse_emp_length)
    df["home_ownership"] = df["home_ownership"].apply(clean_home_ownership)

    # Features derivadas
    df["fico_avg"] = (df["fico_range_low"] + df["fico_range_high"]) / 2
    df["credit_history_yrs"] = (
        df["issue_d"] - df["earliest_cr_line"]
    ).dt.days / 365.25
    df["log_annual_inc"] = np.log1p(df["annual_inc"].clip(lower=0))
    df["loan_to_income"] = df["loan_amnt"] / df["annual_inc"].clip(lower=1)

    # Regionalización
    df["region"] = df["addr_state"].map(REGION_MAP).fillna("Other")

    # Dummy de missingness para las cols seleccionadas
    for col, _ in IMPUTE_WITH_DUMMY_COLS:
        df[f"{col}_missing"] = df[col].isna().astype("int8")

    return df


def fit_imputation(df_train):
    """Calcula medianas en train. Devuelve dict {col: valor}."""
    imputes = {}
    for col in IMPUTE_MEDIAN_COLS:
        imputes[col] = float(df_train[col].median())
    for col, strategy in IMPUTE_WITH_DUMMY_COLS:
        if strategy == "median":
            imputes[col] = float(df_train[col].median())
        elif strategy == "zero":
            imputes[col] = 0.0
        else:
            raise ValueError(strategy)
    # emp_length_num también se imputa con mediana si no está en la lista aún
    return imputes


def apply_imputation(df, imputes):
    df = df.copy()
    for col, value in imputes.items():
        df[col] = df[col].fillna(value)
    return df


def fit_winsorization(df_train, cols, pct=0.99):
    """Calcula umbral del percentil `pct` en train para cada col de `cols`."""
    thresholds = {}
    for col in cols:
        thresholds[col] = float(df_train[col].quantile(pct))
    return thresholds


def apply_winsorization(df, thresholds):
    """
    Capa los valores extremos al umbral. Aplicamos winsorización unilateral
    (solo cola derecha) porque los problemas identificados en EDA son todos
    en la cola derecha (max extremos, min en 0 es interpretable).
    """
    df = df.copy()
    for col, thresh in thresholds.items():
        df[col] = df[col].clip(upper=thresh)
    return df


def encode_onehot(df, oh_cols, template_cols=None):
    """
    One-hot encoding. Si template_cols está dado, alinea a esas columnas
    (crea las que falten con ceros, quita las que sobren).
    """
    dummies = pd.get_dummies(df[oh_cols], prefix=oh_cols, dtype="int8")
    if template_cols is not None:
        # Alinear a template (train): asegura que val/test tengan exactamente
        # las mismas columnas que train
        dummies = dummies.reindex(columns=template_cols, fill_value=0)
    return dummies


def build_X(df, oh_cols, oh_template=None):
    """
    Construye la matriz X de features numéricos para el modelo.
    """
    # Features continuos / numéricos directos
    num_features = [
        "loan_amnt", "term_months", "emp_length_num",
        "annual_inc", "log_annual_inc", "loan_to_income",
        "dti", "delinq_2yrs", "fico_avg", "credit_history_yrs",
        "inq_last_6mths", "open_acc", "pub_rec", "revol_bal", "revol_util",
        "total_acc", "mort_acc", "pub_rec_bankruptcies", "tax_liens",
        "acc_now_delinq", "chargeoff_within_12_mths",
        "collections_12_mths_ex_med",
    ]
    # Dummies de missingness
    missing_dummies = [f"{col}_missing" for col, _ in IMPUTE_WITH_DUMMY_COLS]

    X_num = df[num_features + missing_dummies].astype(float)
    X_oh = encode_onehot(df, oh_cols, template_cols=oh_template)

    # Concatenamos
    X = pd.concat([X_num.reset_index(drop=True), X_oh.reset_index(drop=True)], axis=1)
    return X


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Cargar splits originales
    print("[1/6] Cargando splits originales...")
    df_train = pd.read_parquet(f"{PROCESSED_DIR}/train.parquet")
    df_val = pd.read_parquet(f"{PROCESSED_DIR}/val.parquet")
    df_test = pd.read_parquet(f"{PROCESSED_DIR}/test.parquet")
    print(f"       train: {len(df_train):,} | val: {len(df_val):,} | test: {len(df_test):,}")

    # Limpieza + feature engineering + filtro temporal
    print(f"[2/6] Limpieza + filtro temporal [{YEAR_MIN}-{YEAR_MAX}]...")
    df_train = clean_raw(df_train)
    df_val = clean_raw(df_val)
    df_test = clean_raw(df_test)
    print(f"       train: {len(df_train):,} | val: {len(df_val):,} | test: {len(df_test):,}")
    print(f"       default rate: "
          f"train={df_train['default'].mean():.4f} | "
          f"val={df_val['default'].mean():.4f} | "
          f"test={df_test['default'].mean():.4f}")

    # Fit imputación en train, aplicar a los tres
    print("[3/6] Fit imputación en train, aplicar a val/test...")
    imputes = fit_imputation(df_train)
    df_train = apply_imputation(df_train, imputes)
    df_val = apply_imputation(df_val, imputes)
    df_test = apply_imputation(df_test, imputes)
    print(f"       imputaciones: {imputes}")

    # Winsorización de cola derecha (outliers extremos) — ver DATA_CONTEXT.md
    print(f"[3b] Winsorización cola derecha al P{int(WINSORIZE_PCT*100)} (fit en train)...")
    # Recalculamos loan_to_income post-imputación para consistencia
    for d in [df_train, df_val, df_test]:
        d["loan_to_income"] = d["loan_amnt"] / d["annual_inc"].clip(lower=1)
    winsor_thresh = fit_winsorization(df_train, WINSORIZE_COLS, pct=WINSORIZE_PCT)
    print(f"       umbrales P{int(WINSORIZE_PCT*100)}:")
    for c, v in winsor_thresh.items():
        print(f"         {c}: {v:.2f}")
    df_train = apply_winsorization(df_train, winsor_thresh)
    df_val = apply_winsorization(df_val, winsor_thresh)
    df_test = apply_winsorization(df_test, winsor_thresh)

    # Recalculamos log_annual_inc post-winsorización
    for d in [df_train, df_val, df_test]:
        d["log_annual_inc"] = np.log1p(d["annual_inc"].clip(lower=0))

    # Construir X,y,meta de cada split
    print("[4/6] Construcción de X,y,meta...")
    # Primero X_train para sacar el template de one-hot
    X_train_tmp = build_X(df_train, OH_COLS, oh_template=None)
    oh_template = [c for c in X_train_tmp.columns if any(c.startswith(f"{col}_") for col in OH_COLS)]

    X_train = build_X(df_train, OH_COLS, oh_template=oh_template)
    X_val = build_X(df_val, OH_COLS, oh_template=oh_template)
    X_test = build_X(df_test, OH_COLS, oh_template=oh_template)

    y_train = df_train["default"].astype("int8").values
    y_val = df_val["default"].astype("int8").values
    y_test = df_test["default"].astype("int8").values

    # Meta: cols preservadas + target
    def _build_meta(df):
        cols = [c for c in META_COLS if c in df.columns]
        m = df[cols].reset_index(drop=True).copy()
        m["default"] = df["default"].values
        return m

    meta_train = _build_meta(df_train)
    meta_val = _build_meta(df_val)
    meta_test = _build_meta(df_test)

    print(f"       X_train shape: {X_train.shape}")
    print(f"       X_val shape:   {X_val.shape}")
    print(f"       X_test shape:  {X_test.shape}")
    print(f"       default rate (confirma consistencia con meta):")
    print(f"         train: y_train.mean()={y_train.mean():.4f} "
          f"== meta_train.default.mean()={meta_train['default'].mean():.4f}")

    # Verificación: no NaN en X
    for name, X in [("train", X_train), ("val", X_val), ("test", X_test)]:
        n_nan = X.isna().sum().sum()
        if n_nan > 0:
            nan_cols = X.columns[X.isna().any()].tolist()
            print(f"       WARNING: X_{name} tiene {n_nan} NaN en cols: {nan_cols}")
        else:
            print(f"       X_{name}: 0 NaN ✓")

    # Guardar
    print(f"[5/6] Guardando en {PROCESSED_DIR}/...")
    X_train.to_parquet(f"{PROCESSED_DIR}/X_train.parquet", index=False)
    X_val.to_parquet(f"{PROCESSED_DIR}/X_val.parquet", index=False)
    X_test.to_parquet(f"{PROCESSED_DIR}/X_test.parquet", index=False)

    np.save(f"{PROCESSED_DIR}/y_train.npy", y_train)
    np.save(f"{PROCESSED_DIR}/y_val.npy", y_val)
    np.save(f"{PROCESSED_DIR}/y_test.npy", y_test)

    meta_train.to_parquet(f"{PROCESSED_DIR}/meta_train.parquet", index=False)
    meta_val.to_parquet(f"{PROCESSED_DIR}/meta_val.parquet", index=False)
    meta_test.to_parquet(f"{PROCESSED_DIR}/meta_test.parquet", index=False)

    # Metadatos para reproducibilidad
    metadata = {
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "n_train": int(len(X_train)),
        "n_val": int(len(X_val)),
        "n_test": int(len(X_test)),
        "n_features": int(X_train.shape[1]),
        "feature_names": X_train.columns.tolist(),
        "imputation_values": {k: float(v) for k, v in imputes.items()},
        "winsorization_pct": WINSORIZE_PCT,
        "winsorization_thresholds": winsor_thresh,
        "region_map_size": len(set(REGION_MAP.values())),
        "default_rate_train": float(y_train.mean()),
        "default_rate_val": float(y_val.mean()),
        "default_rate_test": float(y_test.mean()),
    }
    with open(f"{PROCESSED_DIR}/preprocessing_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Listado
    print(f"[6/6] Archivos en {PROCESSED_DIR}/:")
    for f in sorted(os.listdir(PROCESSED_DIR)):
        size = os.path.getsize(f"{PROCESSED_DIR}/{f}") / 1e6
        print(f"    {f}: {size:.2f} MB")


if __name__ == "__main__":
    main()
