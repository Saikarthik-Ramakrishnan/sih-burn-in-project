import React, { useMemo } from "react";
import { adaptPredictionResponse } from "../lib/dashboardAdapter.js";

const show = (value) => value === null || value === undefined ? "N/A" : String(value);

const withUnit = (measurement) => {
  if (!measurement) return "N/A";
  return measurement.value === null || measurement.value === undefined
    ? `N/A ${measurement.unit}`
    : `${measurement.value} ${measurement.unit}`;
};

const intervalText = (interval) => {
  if (!interval || interval.lower === null || interval.upper === null) return `N/A ${interval?.unit || ""}`.trim();
  return `${interval.lower}-${interval.upper} ${interval.unit}`;
};

/** Pass prediction API JSON directly as predictionResponse. */
export default function PredictionDashboard({ predictionResponse, LeakageChart }) {
  const dashboard = useMemo(() => adaptPredictionResponse(predictionResponse), [predictionResponse]);

  return (
    <section aria-label="MLCC prediction dashboard">
      <div className="batch-summary">
        <span>Total: {dashboard.batchSummary.total}</span>
        <span>Scored: {dashboard.batchSummary.scored}</span>
        <span>Unscored: {dashboard.batchSummary.unscored}</span>
        {Object.entries(dashboard.batchSummary.recommendationCounts).map(([name, count]) => (
          <span key={name}>{name}: {count}</span>
        ))}
      </div>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Current leakage</th>
            <th>Limit</th>
            <th>Forecast</th>
            <th>Prediction interval</th>
            <th>Anomaly</th>
            <th>Recommendation</th>
            <th>Reasons</th>
            <th>Scoring status</th>
          </tr>
        </thead>
        <tbody>
          {dashboard.componentTable.map((row) => (
            <tr key={row.componentId}>
              <td>{show(row.componentId)}</td>
              <td>{withUnit(row.currentLeakage)}</td>
              <td>{withUnit(row.leakageLimit)}</td>
              <td>{withUnit(row.forecast)}</td>
              <td>{intervalText(row.predictionInterval)}</td>
              <td>{show(row.anomalyFlag)}</td>
              <td>{show(row.recommendation)}</td>
              <td>{Array.isArray(row.reasons) ? row.reasons.join(", ") : show(row.reasons)}</td>
              <td>{row.scoringStatus}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {LeakageChart ? <LeakageChart data={dashboard.chartData} /> : null}
    </section>
  );
}
