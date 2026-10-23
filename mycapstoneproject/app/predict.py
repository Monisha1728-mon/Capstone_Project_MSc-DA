import numpy as np
import pandas as pd

from models_loader import model, encoder, feature_list

# ---------------------------------------------------------
# Original predictor columns
# ---------------------------------------------------------

NUMERIC_COLUMNS = [
    "year",
    "age",
    "assessed",
    "appropriate_fit",
    "user_trained",
    "locally_manufactured",
    "maintenance_available",
    "device_broken",
    "cost_affordable",
    "insurance_covered",
    "financial_barrier",
    "availability_barrier",
    "distance_barrier",
    "functional_improvement",
    "independence_improved",
    "participation_improved",
    "satisfaction",
    "unmet_need",
]


CATEGORICAL_COLUMNS = [
    "scenario",
    "setting",
    "sex",
    "device_needed",
    "disability_type",
    "device_source",
]


ALL_PREDICTOR_COLUMNS = NUMERIC_COLUMNS + CATEGORICAL_COLUMNS


# ---------------------------------------------------------
# Convert Yes/No values to 0/1
# ---------------------------------------------------------


def to_binary(value, field_name):
    """
    Convert form values into the 0/1 representation
    used by the dataset.
    """

    value = str(value).strip().lower()

    mapping = {
        "0": 0,
        "1": 1,
        "no": 0,
        "yes": 1,
        "false": 0,
        "true": 1,
    }

    if value not in mapping:
        raise ValueError(f"Invalid value for '{field_name}': {value}")

    return mapping[value]


# ---------------------------------------------------------
# Build the original 24 predictor columns
# ---------------------------------------------------------


def prepare_input(form_data):
    """
    Convert Flask form data into the same 24 predictor
    columns used before one-hot encoding.
    """

    row = {}

    # Numeric / binary columns
    for column in NUMERIC_COLUMNS:

        if column not in form_data:
            raise ValueError(f"Missing required field: {column}")

        value = form_data[column]

        if column in {
            "assessed",
            "appropriate_fit",
            "user_trained",
            "locally_manufactured",
            "maintenance_available",
            "device_broken",
            "cost_affordable",
            "insurance_covered",
            "financial_barrier",
            "availability_barrier",
            "distance_barrier",
            "functional_improvement",
            "independence_improved",
            "participation_improved",
            "satisfaction",
            "unmet_need",
        }:
            row[column] = to_binary(value, column)

        elif column == "year":
            row[column] = int(value)

        elif column == "age":
            row[column] = float(value)

    # Categorical columns
    for column in CATEGORICAL_COLUMNS:

        if column not in form_data:
            raise ValueError(f"Missing required field: {column}")

        value = str(form_data[column]).strip()

        if not value:
            raise ValueError(f"Please select a value for: {column}")

        row[column] = value

    return pd.DataFrame([row], columns=ALL_PREDICTOR_COLUMNS)


# ---------------------------------------------------------
# Transform categorical values into encoded features
# ---------------------------------------------------------


def transform_features(input_df):

    numeric_df = input_df[NUMERIC_COLUMNS].astype(float)

    categorical_df = input_df[CATEGORICAL_COLUMNS].astype(str)

    # encoder.pkl was created for the categorical columns.
    encoded = encoder.transform(categorical_df)

    # Convert sparse output if necessary
    if hasattr(encoded, "toarray"):
        encoded = encoded.toarray()

    encoded_df = pd.DataFrame(
        encoded,
        columns=encoder.get_feature_names_out(CATEGORICAL_COLUMNS),
        index=input_df.index,
    )

    # Combine numeric + encoded categorical columns
    final_df = pd.concat([numeric_df, encoded_df], axis=1)

    # -----------------------------------------------------
    # Make absolutely sure the model receives the exact
    # feature order stored in feature_list.json.
    # -----------------------------------------------------

    missing_features = [
        feature for feature in feature_list if feature not in final_df.columns
    ]

    if missing_features:
        raise ValueError("Missing encoded features: " + ", ".join(missing_features))

    final_df = final_df[feature_list]

    if final_df.shape[1] != 55:
        raise ValueError(
            f"Model input has {final_df.shape[1]} features. " f"Expected exactly 55."
        )

    return final_df


# ---------------------------------------------------------
# Risk level
# ---------------------------------------------------------


def get_risk_level(probability):
    """
    Convert abandonment probability into a simple
    Low / Medium / High presentation label.

    Current initial thresholds:
        < 0.30  -> Low
        < 0.60  -> Medium
        >= 0.60 -> High

    These are presentation thresholds and can be tuned
    later using validation results.
    """

    if probability < 0.30:
        return "Low"

    if probability < 0.60:
        return "Medium"

    return "High"


# ---------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------


def predict(form_data):

    # -----------------------------------------------------
    # Q1 is handled in app.py.
    # Only received-device users reach this function.
    # -----------------------------------------------------

    input_df = prepare_input(form_data)

    # Convert to exact 55-feature representation
    X = transform_features(input_df)

    # -----------------------------------------------------
    # Prediction
    # -----------------------------------------------------

    prediction = int(model.predict(X)[0])

    # Probability of class 1 = abandonment
    probabilities = model.predict_proba(X)[0]

    classes = list(model.classes_)

    if 1 in classes:
        abandonment_index = classes.index(1)
        abandonment_probability = float(probabilities[abandonment_index])
    else:
        raise ValueError("The trained model does not contain class 1 " "(abandoned).")

    # -----------------------------------------------------
    # Presentation
    # -----------------------------------------------------

    risk = get_risk_level(abandonment_probability)

    risk_score = round(abandonment_probability * 100, 2)

    return {
        "prediction": prediction,
        "risk": risk,
        "risk_score": risk_score,
        "probability": risk_score,
        "message": (f"Estimated abandonment probability: " f"{risk_score}%"),
        "features_used": 55,
    }
