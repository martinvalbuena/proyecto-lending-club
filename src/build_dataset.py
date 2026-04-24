"""
Construcción del dataset procesado a partir del CSV crudo de Lending Club.

Pipeline:
  1. Lectura chunked con columnas seleccionadas
  2. Filtrado de loan_status para construir target binario `default`
  3. Muestreo estratificado a N_SAMPLE filas (preservando tasa de default)
  4. Splits train/val/test 70/15/15 estratificados
  5. Guardado como parquet en data/processed/

Uso:
    python src/build_dataset.py

Reproducibilidad: RANDOM_SEED=42.
"""
import os
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
RAW_PATH = "data/raw/accepted_2007_to_2018Q4.csv.gz"
PROCESSED_DIR = "data/processed"
N_SAMPLE = 200_000        # muestreo estratificado objetivo
RANDOM_SEED = 42
CHUNK_SIZE = 200_000

# Columnas seleccionadas — cubren target, pricing, features al origen,
# historial crediticio y algunas post-origen para EDA. Excluimos columnas
# ~100% nulas (hardship_*, settlement_*, sec_app_*, joint_*) y IDs.
COLS_KEEP = [
    # Target & pricing
    "loan_status", "loan_amnt", "int_rate", "grade", "sub_grade", "term", "installment",
    # Loan metadata
    "issue_d", "purpose", "title", "application_type", "initial_list_status",
    "disbursement_method",
    # Borrower demographics / employment
    "emp_title", "emp_length", "home_ownership", "annual_inc", "verification_status",
    "addr_state", "zip_code",
    # Credit history al origen
    "dti", "delinq_2yrs", "earliest_cr_line", "fico_range_low", "fico_range_high",
    "inq_last_6mths", "open_acc", "pub_rec", "revol_bal", "revol_util", "total_acc",
    "mort_acc", "pub_rec_bankruptcies", "tax_liens", "acc_now_delinq",
    "chargeoff_within_12_mths", "collections_12_mths_ex_med",
    # Post-origen (útiles para EDA / validación, NO para features ML)
    "total_pymnt", "total_rec_prncp", "total_rec_int", "recoveries",
    "last_pymnt_d", "last_fico_range_low", "last_fico_range_high",
]

# Mapeo de loan_status → target binario
DEFAULT_STATUSES = {"Charged Off", "Default"}
PAID_STATUSES = {"Fully Paid"}


def build_target(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra loan_status a conjunto binario y crea columna `default`."""
    keep = df["loan_status"].isin(DEFAULT_STATUSES | PAID_STATUSES)
    df = df.loc[keep].copy()
    df["default"] = df["loan_status"].isin(DEFAULT_STATUSES).astype("int8")
    return df


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    rng = np.random.RandomState(RANDOM_SEED)

    # -----------------------------------------------------------------------
    # Paso 1-2: Lectura chunked + filtrado de target
    # -----------------------------------------------------------------------
    print(f"[1/5] Leyendo {RAW_PATH} por chunks de {CHUNK_SIZE:,} filas...")
    t0 = time.time()
    frames = []
    n_read = 0
    for i, chunk in enumerate(pd.read_csv(
        RAW_PATH, usecols=COLS_KEEP, chunksize=CHUNK_SIZE, low_memory=False
    )):
        n_read += len(chunk)
        chunk = build_target(chunk)
        frames.append(chunk)
        print(f"    chunk {i+1}: leídas {n_read:,} filas acum | "
              f"retenidas {sum(len(f) for f in frames):,} post-filtro")
    df = pd.concat(frames, ignore_index=True)
    del frames
    print(f"[1/5] OK en {time.time()-t0:.1f}s → {len(df):,} filas × {df.shape[1]} cols")
    print(f"       default rate: {df['default'].mean():.4f}")

    # -----------------------------------------------------------------------
    # Paso 3: Muestreo estratificado
    # -----------------------------------------------------------------------
    print(f"[2/5] Muestreo estratificado a {N_SAMPLE:,} filas por `default`...")
    frac = N_SAMPLE / len(df)
    df_sample = (df.groupby("default", group_keys=False)
                   .sample(frac=frac, random_state=RANDOM_SEED))
    print(f"[2/5] OK → {len(df_sample):,} filas | "
          f"default rate: {df_sample['default'].mean():.4f}")

    # -----------------------------------------------------------------------
    # Paso 4: Splits 70/15/15 estratificados
    # -----------------------------------------------------------------------
    print("[3/5] Split train(70) / val(15) / test(15) estratificado por `default`...")
    df_train, df_temp = train_test_split(
        df_sample, test_size=0.30,
        stratify=df_sample["default"], random_state=RANDOM_SEED,
    )
    df_val, df_test = train_test_split(
        df_temp, test_size=0.50,
        stratify=df_temp["default"], random_state=RANDOM_SEED,
    )
    for name, d in [("train", df_train), ("val", df_val), ("test", df_test)]:
        print(f"    {name:5s}: {len(d):>7,} filas | "
              f"default rate: {d['default'].mean():.4f}")

    # -----------------------------------------------------------------------
    # Paso 5: Guardado
    # -----------------------------------------------------------------------
    print(f"[4/5] Guardando en {PROCESSED_DIR}/...")
    df_train.to_parquet(f"{PROCESSED_DIR}/train.parquet", index=False)
    df_val.to_parquet(f"{PROCESSED_DIR}/val.parquet", index=False)
    df_test.to_parquet(f"{PROCESSED_DIR}/test.parquet", index=False)

    # Guardamos también la muestra completa (pre-split) por conveniencia
    df_sample.to_parquet(f"{PROCESSED_DIR}/sample_200k.parquet", index=False)

    # Stats resumen
    stats = {
        "n_raw_total": int(n_read),
        "n_post_filter": int(len(df)),
        "n_sample": int(len(df_sample)),
        "n_train": int(len(df_train)),
        "n_val": int(len(df_val)),
        "n_test": int(len(df_test)),
        "default_rate_raw": float(df["default"].mean()),
        "default_rate_sample": float(df_sample["default"].mean()),
        "random_seed": RANDOM_SEED,
    }
    import json
    with open(f"{PROCESSED_DIR}/build_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print(f"[5/5] Listo. Archivos en {PROCESSED_DIR}/:")
    for f in sorted(os.listdir(PROCESSED_DIR)):
        size = os.path.getsize(f"{PROCESSED_DIR}/{f}") / 1e6
        print(f"    {f}: {size:.1f} MB")


if __name__ == "__main__":
    main()
