
--Se crea el modelo ARIMA para predecir la cantidad de viajes diarios 
CREATE OR REPLACE MODEL
  `PROJECT_ID.raw_data.cta_ridership_model` OPTIONS(MODEL_TYPE='ARIMA',
    TIME_SERIES_TIMESTAMP_COL='service_date',
    TIME_SERIES_DATA_COL='total_rides',
    HOLIDAY_REGION='us') AS
SELECT
  service_date, total_rides
FROM
  `PROJECT_ID.raw_data.cta_ridership`

--La primera fila de la tabla contendrá el mejor modelo, que es el que tiene el valor de AIC más bajo.
--Este modelo lo utilizaremos para hacer las predicciones con ML.FORECAST
SELECT
  *
FROM
  ML.EVALUATE(MODEL `PROJECT_ID.raw_data.cta_ridership_model`)

--Predicciones para los próximos 7 días
SELECT
  *
FROM
  ML.FORECAST(MODEL `PROJECT_ID.raw_data.cta_ridership_model`,
    STRUCT(7 AS horizon))

--Anomalia identificadas en los datos históricos
SELECT
  *
FROM
  ML.DETECT_ANOMALIES (
   MODEL `PROJECT_ID.raw_data.cta_ridership_model`,
   STRUCT(0.9 AS anomaly_prob_threshold)
  )
  WHERE
is_anomaly = TRUE
