const DEFAULT_LEAKAGE_UNIT = "uA";
const DEFAULT_TIME_UNIT = "hours";

function firstDefined(...values) {
  return values.find((value) => value !== undefined);
}

function asArray(value) {
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null) return [];
  return [value];
}

function isPlainRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function asNullableNumber(value) {
  if (value === undefined || value === null || value === "") return null;
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
}

function asNullableBoolean(value) {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "yes", "y", "1", "anomaly", "flagged"].includes(normalized)) return true;
    if (["false", "no", "n", "0", "normal", "ok"].includes(normalized)) return false;
  }
  return null;
}

function getUnit(source, valueField, fallback = DEFAULT_LEAKAGE_UNIT) {
  return firstDefined(
    source?.[`${valueField}_unit`],
    source?.[`${valueField}Unit`],
    source?.unit,
    source?.units,
    fallback,
  );
}

function unwrapValue(source, valueKeys, unitFallback = DEFAULT_LEAKAGE_UNIT) {
  const objectValue = valueKeys.map((key) => source?.[key]).find((value) => {
    return isPlainRecord(value);
  });

  if (objectValue) {
    return {
      value: asNullableNumber(firstDefined(objectValue.value, objectValue.mean, objectValue.p50)),
      unit: firstDefined(objectValue.unit, objectValue.units, unitFallback),
    };
  }

  const key = valueKeys.find((candidate) => source?.[candidate] !== undefined);
  return {
    value: asNullableNumber(key ? source[key] : undefined),
    unit: getUnit(source, key || valueKeys[0], unitFallback),
  };
}

function unwrapInterval(source, fieldKeys, unitFallback = DEFAULT_LEAKAGE_UNIT) {
  const interval = fieldKeys.map((key) => source?.[key]).find((value) => {
    return value && typeof value === "object";
  });

  if (Array.isArray(interval)) {
    return {
      lower: asNullableNumber(interval[0]),
      upper: asNullableNumber(interval[1]),
      unit: unitFallback,
    };
  }

  if (interval) {
    return {
      lower: asNullableNumber(firstDefined(interval.lower, interval.low, interval.l95, interval.p05)),
      upper: asNullableNumber(firstDefined(interval.upper, interval.high, interval.u95, interval.p95)),
      unit: firstDefined(interval.unit, interval.units, unitFallback),
    };
  }

  return {
    lower: asNullableNumber(firstDefined(source?.prediction_interval_lower, source?.forecast_lower, source?.lower_bound)),
    upper: asNullableNumber(firstDefined(source?.prediction_interval_upper, source?.forecast_upper, source?.upper_bound)),
    unit: firstDefined(source?.prediction_interval_unit, source?.forecast_unit, source?.unit, unitFallback),
  };
}

function deriveScoringStatus(component, forecast) {
  const explicitStatus = firstDefined(
    component.scoring_status,
    component.scoringStatus,
    component.score_status,
    component.status,
  );

  if (explicitStatus !== undefined && explicitStatus !== null && explicitStatus !== "") {
    return String(explicitStatus);
  }

  if (component.scored !== undefined && component.scored !== null) {
    return component.scored ? "scored" : "unscored";
  }

  return forecast.value !== null ? "scored" : "unscored";
}

function getComponents(response) {
  if (Array.isArray(response)) return response;
  const payload = firstDefined(response?.data, response?.payload, response);
  if (Array.isArray(payload)) return payload;

  return firstDefined(
    payload?.components,
    payload?.component_predictions,
    payload?.predictions,
    payload?.results,
    payload?.items,
    response?.components,
    response?.component_predictions,
    response?.predictions,
    response?.results,
    response?.items,
    response?.data,
    [],
  );
}

function getComponentList(response) {
  return asArray(getComponents(response)).filter(isPlainRecord);
}

function normalizeReading(reading, componentUnit) {
  const source = reading && typeof reading === "object" ? reading : { value: reading };
  const leakage = unwrapValue(source, ["leakage", "leakage_uA", "current_leakage", "currentLeakage", "value"], componentUnit);
  return {
    kind: "measured",
    time: asNullableNumber(firstDefined(source.hour, source.hours, source.time, source.t, source.x)),
    timeUnit: firstDefined(source.time_unit, source.timeUnit, source.hour_unit, DEFAULT_TIME_UNIT),
    value: leakage.value,
    unit: leakage.unit,
  };
}

function normalizePredictionPoint(point, componentUnit, componentInterval) {
  const source = point && typeof point === "object" ? point : { value: point };
  const forecast = unwrapValue(source, ["forecast", "predicted_leakage", "predictedLeakage", "prediction", "value"], componentUnit);
  const interval = unwrapInterval(source, ["prediction_interval", "predictionInterval", "forecast_interval", "interval"], forecast.unit);
  return {
    kind: "predicted",
    time: asNullableNumber(firstDefined(source.horizon, source.hour, source.hours, source.time, source.t, source.x)),
    timeUnit: firstDefined(source.time_unit, source.timeUnit, source.hour_unit, DEFAULT_TIME_UNIT),
    value: forecast.value,
    unit: forecast.unit,
    intervalLower: interval.lower ?? componentInterval.lower,
    intervalUpper: interval.upper ?? componentInterval.upper,
    intervalUnit: interval.unit ?? componentInterval.unit,
  };
}

function normalizeComponent(component, index) {
  const source = component && typeof component === "object" ? component : {};
  const id = String(firstDefined(source.id, source.component_id, source.componentId, source.serial, index + 1));
  const currentLeakage = unwrapValue(source, ["current_leakage", "currentLeakage", "current", "latest_leakage", "leakage"], DEFAULT_LEAKAGE_UNIT);
  const leakageLimit = unwrapValue(source, ["limit", "leakage_limit", "leakageLimit", "spec_limit", "threshold"], currentLeakage.unit);
  const forecast = unwrapValue(source, ["forecast", "forecast_leakage", "forecastLeakage", "predicted_leakage", "predictedLeakage", "prediction"], currentLeakage.unit);
  const predictionInterval = unwrapInterval(source, ["prediction_interval", "predictionInterval", "forecast_interval", "forecastInterval", "interval"], forecast.unit);
  const recommendation = firstDefined(source.recommendation, source.action, source.decision, null);
  const reasons = asArray(firstDefined(source.reasons, source.reason_codes, source.reasonCodes, source.reason, []))
    .filter((reason) => reason !== undefined && reason !== null && reason !== "")
    .map(String);

  const scoringStatus = deriveScoringStatus(source, forecast);
  const anomalyFlag = asNullableBoolean(firstDefined(source.anomaly_flag, source.anomalyFlag, source.is_anomaly, source.anomaly));
  const rawReadings = firstDefined(source.early_readings, source.earlyReadings, source.readings, source.history, []);
  const rawForecastPoints = firstDefined(source.forecast_points, source.forecastPoints, source.predicted_points, source.predictedPoints, []);
  const measured = asArray(rawReadings).map((reading) => normalizeReading(reading, currentLeakage.unit));
  const predicted = asArray(rawForecastPoints).map((point) => normalizePredictionPoint(point, forecast.unit, predictionInterval));

  if (predicted.length === 0) {
    predicted.push({
      kind: "predicted",
      time: asNullableNumber(firstDefined(source.forecast_horizon, source.forecastHorizon, source.horizon)),
      timeUnit: firstDefined(source.forecast_horizon_unit, source.forecastHorizonUnit, DEFAULT_TIME_UNIT),
      value: forecast.value,
      unit: forecast.unit,
      intervalLower: predictionInterval.lower,
      intervalUpper: predictionInterval.upper,
      intervalUnit: predictionInterval.unit,
    });
  }

  return {
    row: {
      componentId: id,
      currentLeakage,
      leakageLimit,
      forecast,
      predictionInterval,
      anomalyFlag,
      recommendation: recommendation ?? null,
      reasons,
      scoringStatus,
    },
    chart: {
      componentId: id,
      points: [...measured, ...predicted],
    },
  };
}

export function buildComponentTable(predictionResponse) {
  return getComponentList(predictionResponse).map((component, index) => {
    return normalizeComponent(component, index).row;
  });
}

export function buildBatchSummary(componentTable) {
  const rows = asArray(componentTable);
  return rows.reduce(
    (summary, row) => {
      const status = String(row.scoringStatus || "").toLowerCase();
      const recommendationKey = row.recommendation === null ? "null" : String(row.recommendation);

      summary.total += 1;
      if (status === "scored") summary.scored += 1;
      else summary.unscored += 1;

      summary.recommendationCounts[recommendationKey] = (summary.recommendationCounts[recommendationKey] || 0) + 1;
      return summary;
    },
    {
      total: 0,
      scored: 0,
      unscored: 0,
      recommendationCounts: {},
    },
  );
}

export function buildChartData(predictionResponse) {
  return getComponentList(predictionResponse).map((component, index) => {
    return normalizeComponent(component, index).chart;
  });
}

export function buildDashboardTables(predictionResponse) {
  const normalized = getComponentList(predictionResponse).map(normalizeComponent);
  const componentTable = normalized.map((component) => component.row);

  return {
    componentTable,
    batchSummary: buildBatchSummary(componentTable),
    chartData: normalized.map((component) => component.chart),
  };
}

export const adaptPredictionResponse = buildDashboardTables;

export default buildDashboardTables;
