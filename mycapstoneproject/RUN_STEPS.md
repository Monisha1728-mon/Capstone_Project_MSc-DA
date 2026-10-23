# How to run the project

## 1. Install Python
Use Python 3.10 or 3.11 if possible.

## 2. Open terminal in the project folder
Example:
`cd AT-Abandonment-Prediction`

## 3. Create virtual environment
Windows:
`py -m venv venv`
`venv\Scripts\activate`

macOS/Linux:
`python3 -m venv venv`
`source venv/bin/activate`

## 4. Install packages
`python -m pip install --upgrade pip`
`pip install -r requirements.txt`

## 5. Add the real dataset
Copy these files into:
`data/raw/`
- `at_urban.csv`
- `at_rural.csv`
- `at_district.csv`

Do not edit the raw files.

## 6. Prepare data
`python src/preprocess.py`

This creates:
- `data/processed/merged_recipients.csv`
- `data/processed/X_train.csv`
- `data/processed/y_train.csv`
- `data/processed/X_train_smote.csv`
- `data/processed/y_train_smote.csv`
- `data/processed/X_test.csv`
- `data/processed/y_test.csv`
- `models/encoder.pkl`
- `models/feature_list.json`

## 7. Train all three models
`python src/train_models.py`

This trains:
- Logistic Regression
- Random Forest
- Gradient Boosting

## 8. Evaluate and select the deployment model
`python src/evaluate.py`

The evaluation compares Accuracy, Precision, Recall, F1 and ROC-AUC. The project document identifies Logistic Regression as the reference/production model from the reported results. The script also records the best model based on the configured selection rule.

## 9. Run the Flask website
`python app/app.py`

Then open the local address printed by Flask.

## 10. Website flow
Login/Register -> Patient/device form -> Prediction -> SHAP explanation -> Dashboard -> SQLite record.

## 11. PWA
The project includes a manifest and service worker. PWA behavior depends on browser/security context; offline prediction is not automatically guaranteed because the Flask model normally runs on the server.
