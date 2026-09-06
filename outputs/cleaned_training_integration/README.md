# Cleaned training integration

Verified 14,400 readings / 7,200 components / 36 batches against the actual training-file hash recorded by the model. All components score with the saved Isolation Forest + XGBoost models. No retraining was needed.

Teammate percent_change uses percent; production uses fractional change (divide teammate values by 100). Production robust-z calculations retain their numerical scale floors. Screening status is never an input feature or a future-failure label.

Backend: use integrated_train_early.csv with the existing score_mlcc_prototype.py, or screen_readings(readings, bundle, forecast_model='xgboost'). demo_upload_early.csv and demo_response.json provide a one-batch integration example. No API or frontend implementation is changed by this pack.

training_screening_response.json is an integration result on TRAINING data, not an accuracy benchmark. Keep the existing held-out test evaluation for reporting. Original teammate files are preserved under teammate_originals/.
