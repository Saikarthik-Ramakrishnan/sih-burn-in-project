/**
 * Typed API Client for SIH26170 FastAPI Backend.
 */

const API_BASE = '/api/v1';

export async function checkHealth(abortSignal) {
  try {
    const res = await fetch(`${API_BASE}/health/ready`, { signal: abortSignal });
    const data = await res.json();
    return {
      ok: res.ok,
      status: res.status,
      data
    };
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    return {
      ok: false,
      status: 0,
      error: err.message,
      data: {
        ready: false,
        mode: 'standalone_demo',
        capabilities: []
      }
    };
  }
}

export async function getProfiles(abortSignal) {
  try {
    const res = await fetch(`${API_BASE}/profiles`, { signal: abortSignal });
    if (!res.ok) throw new Error(`Profiles check failed: ${res.status}`);
    return await res.json();
  } catch (err) {
    return {
      profiles: [{
        profile_id: 'mlcc_x7r_leakage_ua',
        component_family: 'MLCC_X7R',
        measurement_name: 'leakage_ua',
        measurement_unit: 'uA',
        limit_direction: 'upper',
        status: 'supported',
        required_checkpoint_hours: [0.0, 24.0],
        as_of_hour: 24.0,
        target_hour: 168.0,
        min_peer_group_size: 8,
        usable: true
      }]
    };
  }
}

export async function downloadSampleCsv() {
  const res = await fetch(`${API_BASE}/sample.csv`);
  if (!res.ok) throw new Error(`Failed to fetch sample CSV: ${res.statusText}`);
  return await res.text();
}

export async function screenUpload(earlyFile, outcomeFile = null, forecastModel = 'xgboost_v2', abortSignal = null) {
  const formData = new FormData();
  formData.append('file', earlyFile);
  if (outcomeFile) {
    formData.append('outcome_file', outcomeFile);
  }
  if (forecastModel) {
    formData.append('forecast_model', forecastModel);
  }

  const res = await fetch(`${API_BASE}/screen`, {
    method: 'POST',
    body: formData,
    signal: abortSignal
  });

  const body = await res.json();

  if (!res.ok) {
    const errorPayload = {
      error: body.error || 'UPLOAD_FAILED',
      message: body.message || `Request failed with status ${res.status}`,
      details: body.details || [],
      status: res.status
    };
    throw errorPayload;
  }

  return body;
}
