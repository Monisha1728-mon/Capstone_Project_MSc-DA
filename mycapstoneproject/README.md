# Predicting Assistive Technology Abandonment Using Machine Learning and Explainable AI

Decision-support website using Flask + SQLite + Chart.js + PWA concepts.

## Project basis
- Dataset source described in the project document: HuggingFace `africa-synth-disability-assistive-technology-access-all`
- Three source CSVs: urban, rural, district
- Filter: `device_received == 1`
- Target: `device_abandoned`
- Planned models: Logistic Regression, Random Forest, Gradient Boosting
- Imbalance handling: SMOTE/SMOTENC on training data only
- Model selection: ROC-AUC + F1, with recall prioritized for abandonment detection
- Dashboard: Flask + Chart.js; Power BI is not required
- Explainability: SHAP

## Important
The uploaded project document does not contain the actual CSV dataset files. Therefore this ZIP contains the complete project code/structure, but not fabricated copies of the dataset. Put the three original CSV files in `data/raw/` before training.

## Quick start
1. Create a Python virtual environment.
2. Install `requirements.txt`.
3. Put `at_urban.csv`, `at_rural.csv`, and `at_district.csv` in `data/raw/`.
4. Run:
   `python src/preprocess.py`
5. Run:
   `python src/train_models.py`
6. Run:
   `python src/evaluate.py`
7. Run:
   `python app/app.py`
8. Open the local Flask URL shown in the terminal.

See `RUN_STEPS.md` for detailed instructions.

## Included dataset
The supplied dataset files are included in this ZIP:
- urban: 10,000 rows
- rural: 10,000 rows
- district: 10,000 rows
- combined: 30,000 rows
- after device_received == 1: 2475 rows
- abandoned: 369
- continued: 2106
