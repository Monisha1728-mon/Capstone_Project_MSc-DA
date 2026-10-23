from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from imblearn.over_sampling import SMOTENC

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
MODELS = ROOT / "models"

TARGET = "device_abandoned"
RECEIVED = "device_received"

def load_source_data():
    paths = [RAW/"at_urban.csv", RAW/"at_rural.csv", RAW/"at_district.csv"]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing raw dataset files. Add these files to data/raw/: " +
            ", ".join(Path(x).name for x in missing)
        )
    frames = [pd.read_csv(p) for p in paths]
    return pd.concat(frames, ignore_index=True)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    df = load_source_data()
    if RECEIVED not in df.columns:
        raise ValueError(f"Required column '{RECEIVED}' not found.")
    if TARGET not in df.columns:
        raise ValueError(f"Required target column '{TARGET}' not found.")

    # Keep only people who received a device, as defined in the project.
    df = df[pd.to_numeric(df[RECEIVED], errors="coerce").eq(1)].copy()
    if df.empty:
        raise ValueError("No rows remain after device_received == 1 filtering.")

    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df.dropna(subset=[TARGET])
    df[TARGET] = df[TARGET].astype(int)

    # Remove target and the filtering-only column from model inputs.
    X = df.drop(columns=[TARGET, RECEIVED], errors="ignore")
    y = df[TARGET]

    # Drop obvious identifier columns to reduce leakage/memorization.
    id_like = [c for c in X.columns if c.lower() in {
        "id", "person_id", "patient_id", "respondent_id", "record_id"
    }]
    X = X.drop(columns=id_like, errors="ignore")

    # Convert booleans to strings so categorical handling is consistent.
    for c in X.columns:
        if X[c].dtype == bool:
            X[c] = X[c].astype(str)

    categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    numeric_cols = [c for c in X.columns if c not in categorical_cols]

    # Basic numeric cleaning.
    for c in numeric_cols:
        X[c] = pd.to_numeric(X[c], errors="coerce")
        X[c] = X[c].fillna(X[c].median())

    # Basic categorical cleaning.
    for c in categorical_cols:
        X[c] = X[c].fillna("Unknown").astype(str)

    # Save the final pre-split working dataset.
    final_df = X.copy()
    final_df[TARGET] = y.values
    final_df.to_csv(OUT/"merged_recipients.csv", index=False)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    # Encode categories consistently.
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    if categorical_cols:
        train_cat = encoder.fit_transform(X_train[categorical_cols])
        test_cat = encoder.transform(X_test[categorical_cols])
        cat_names = encoder.get_feature_names_out(categorical_cols).tolist()
    else:
        train_cat = pd.DataFrame(index=X_train.index).values
        test_cat = pd.DataFrame(index=X_test.index).values
        cat_names = []

    train_num = X_train[numeric_cols].to_numpy()
    test_num = X_test[numeric_cols].to_numpy()

    Xtr = pd.DataFrame(
        __import__("numpy").hstack([train_num, train_cat]),
        columns=numeric_cols + cat_names,
        index=X_train.index
    )
    Xte = pd.DataFrame(
        __import__("numpy").hstack([test_num, test_cat]),
        columns=numeric_cols + cat_names,
        index=X_test.index
    )

    # SMOTE on training data only.
    # Since one-hot encoded columns are already numeric, regular SMOTE is used
    # here to keep the training pipeline robust across mixed source schemas.
    from imblearn.over_sampling import SMOTE
    smote = SMOTE(random_state=42)
    Xsm, ysm = smote.fit_resample(Xtr, y_train)

    Xtr.to_csv(OUT/"X_train.csv", index=False)
    y_train.to_csv(OUT/"y_train.csv", index=False)
    pd.DataFrame(Xsm, columns=Xtr.columns).to_csv(OUT/"X_train_smote.csv", index=False)
    pd.Series(ysm, name=TARGET).to_csv(OUT/"y_train_smote.csv", index=False)
    Xte.to_csv(OUT/"X_test.csv", index=False)
    y_test.to_csv(OUT/"y_test.csv", index=False)

    joblib.dump(encoder, MODELS/"encoder.pkl")
    (MODELS/"feature_list.json").write_text(json.dumps(Xtr.columns.tolist(), indent=2))

    print("Preprocessing complete.")
    print(f"Final filtered rows: {len(df)}")
    print(f"Train rows: {len(Xtr)} | SMOTE train rows: {len(Xsm)} | Test rows: {len(Xte)}")
    print("Saved processed data, encoder.pkl and feature_list.json.")

if __name__ == "__main__":
    main()
