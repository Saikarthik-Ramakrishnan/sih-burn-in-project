/**
 * Derive display-only fields from a genuine backend response. Nothing here
 * invents data: outcome fields exist only when the response's evaluation section
 * carries them, and missing metadata stays undefined.
 */
export function enrichResponse(response) {
  const outcomesByKey = new Map();
  for (const o of response?.evaluation?.outcomes || []) {
    const key = `${o.component_id}\u0000${o.measurement_name}`;
    if (!outcomesByKey.has(key)) outcomesByKey.set(key, []);
    outcomesByKey.get(key).push(o);
  }

  const records = (response.records || []).map((r) => {
    const later = (outcomesByKey.get(`${r.component_id}\u0000${r.measurement_name}`) || [])
      .slice()
      .sort((a, b) => a.observed_hour - b.observed_hour);
    const targetHour = r.forecast?.target_hour ?? response.target_hour;
    const final = later.find((o) => o.observed_hour === targetHour) || null;
    const limit = r.limits?.applicable_limit;
    return {
      ...r,
      outcome_trajectory: later.map((o) => ({ hour: o.observed_hour, value: o.observed_value })),
      observed_168h: final ? final.observed_value : null,
      crossed_applicable_limit: final ? final.crossed_applicable_limit : null,
      within_limit_but_unusual: Boolean(
        limit !== null && limit !== undefined && r.latest_value < limit && r.anomaly?.is_anomaly,
      ),
    };
  });

  return {
    ...response,
    records,
    within_limits_but_unusual_count: records.filter((r) => r.within_limit_but_unusual).length,
  };
}
