# Dashboard Adapter Field Dictionary

`buildDashboardTables(predictionResponse)` returns `{ componentTable, batchSummary, chartData }`.

The adapter only reshapes prediction output for the dashboard. It does not calculate risk scores, alter model forecasts, fill missing predictions, or change recommendations.

## Component Table

| Field | Type | Meaning |
|---|---|---|
| `componentId` | string | Stable component identifier from the prediction response. |
| `currentLeakage.value` | number \| null | Latest/current leakage value. |
| `currentLeakage.unit` | string | Current leakage unit, defaulting to `uA` when the response omits it. |
| `leakageLimit.value` | number \| null | Leakage threshold/spec limit supplied by the response. |
| `leakageLimit.unit` | string | Limit unit, defaulting to the leakage unit. |
| `forecast.value` | number \| null | Forecast leakage value supplied by the prediction response. Missing predictions stay `null`. |
| `forecast.unit` | string | Forecast unit, defaulting to the leakage unit. |
| `predictionInterval.lower` | number \| null | Lower forecast interval bound supplied by the prediction response. |
| `predictionInterval.upper` | number \| null | Upper forecast interval bound supplied by the prediction response. |
| `predictionInterval.unit` | string | Prediction interval unit. |
| `anomalyFlag` | boolean \| null | Anomaly flag supplied by the prediction response. |
| `recommendation` | string \| null | Recommendation supplied by the prediction response. Missing recommendations stay `null`. |
| `reasons` | string[] | Reason text or reason codes supplied by the prediction response. |
| `scoringStatus` | string | Scoring state, usually `scored` or `unscored`. Explicit response status is preserved; otherwise missing forecast values are treated as `unscored`. |

## Batch Summary

| Field | Type | Meaning |
|---|---|---|
| `total` | number | Count of all components, including unscored components. |
| `scored` | number | Count of rows whose `scoringStatus` is `scored`. |
| `unscored` | number | Count of rows whose `scoringStatus` is not `scored`. |
| `recommendationCounts` | object | Counts grouped by exact recommendation string. Missing recommendations are counted under the string key `"null"` so no row disappears. |

## Chart Data

| Field | Type | Meaning |
|---|---|---|
| `componentId` | string | Component identifier matching `componentTable.componentId`. |
| `points[].kind` | `"measured"` \| `"predicted"` | Distinguishes early readings from forecast points. |
| `points[].time` | number \| null | Measurement or forecast time. |
| `points[].timeUnit` | string | Time unit, defaulting to `hours`. |
| `points[].value` | number \| null | Leakage value. Missing forecasts stay `null`. |
| `points[].unit` | string | Leakage unit. |
| `points[].intervalLower` | number \| null | Predicted point lower interval. Present on predicted points. |
| `points[].intervalUpper` | number \| null | Predicted point upper interval. Present on predicted points. |
| `points[].intervalUnit` | string | Unit for predicted interval bounds. |

## Frontend Contract Agreed For Designer Review

- Tables display explicit value/unit pairs instead of unitless numbers.
- Unscored components remain visible in the component table and chart data.
- Missing forecasts, interval bounds, anomaly flags, and recommendations are represented as `null`.
- Recommendations are passed through exactly as supplied by the prediction response.
- Chart consumers can style measured and predicted data via `points[].kind`.
