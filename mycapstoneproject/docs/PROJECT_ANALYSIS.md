# Project understanding

## Core objective
Predict whether a person who received an assistive technology device is likely to abandon it, then provide an explanation and decision-support dashboard.

## ML pipeline
Raw urban/rural/district CSVs -> filter device recipients -> clean/encode -> stratified 80/20 split -> SMOTE on training only -> train 3 classifiers -> evaluate -> select deployment model.

## Reported results in the supplied document
Random Forest: Accuracy 70.5%, Precision 25.0%, Recall 48.6%, F1 0.330, ROC-AUC 0.758
Logistic Regression: Accuracy 71.9%, Precision 27.0%, Recall 51.4%, F1 0.353, ROC-AUC 0.777
Gradient Boosting: Accuracy 75.8%, Precision 26.5%, Recall 35.1%, F1 0.302, ROC-AUC 0.762

The supplied document identifies Logistic Regression as the reference/production model and Random Forest as useful for tree-based SHAP explainability.

## Important implementation note
The source document states the exact dataset fields conceptually, but it does not include the actual CSVs or a complete categorical-to-numeric form mapping. Therefore the website form in this ZIP deliberately avoids inventing those mappings. Once the real CSVs are supplied, `preprocess.py` produces the exact feature schema in `models/feature_list.json`, and the form can be mapped to it.

## Verified uploaded dataset
The three supplied CSVs were inspected directly. Each has 10,000 rows and 27 columns. Combined they have 30,000 rows. Filtering `device_received == 1` gives 2475 rows: 369 abandoned and 2,106 continued. The target and field names in the pipeline therefore match the supplied files.
