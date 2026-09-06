# SIH26170 demonstration reliability checklist

## Runtime rule

```text
Local browser -> one local FastAPI/Uvicorn process -> bundled trusted models
```

No internet, cloud API, remote database, Node server or live supervised-model
training may be required.

## Build freeze

- Freeze exact Python and npm dependencies.
- Build and package the Vite static bundle.
- Freeze model artifacts and SHA-256 checksums.
- Freeze one verified CSV and its expected assertions.
- Record Python, OS, browser and library versions.
- Stop feature changes at least 24 hours before judging.

## Automated preflight

One command must:

1. verify Python and dependency locks;
2. verify model/calibration checksums;
3. verify frontend static files;
4. start the app on an available local port;
5. wait for `/api/v1/health/ready`;
6. upload the golden CSV through the real HTTP endpoint;
7. assert schema and model versions;
8. assert the known degrading component is flagged;
9. enforce the rehearsed laptop-specific latency budget;
10. shut down cleanly and report pass/fail.

Do not use a precomputed JSON response for this test.

## Required tests

- Domain unit tests
- CSV validation tests
- Future-data leakage regression test
- Batch-split leakage test
- Model-artifact load test
- Pydantic response-contract test
- FastAPI multipart upload test
- Malformed CSV integration test
- Frontend result/error-state tests
- One Playwright golden-upload test

## Day-before rehearsal

- Perform three consecutive cold starts.
- Run once with Wi-Fi disabled.
- Test the projector resolution or 1024×768 fallback.
- Test mouse and keyboard navigation.
- Upload a malformed CSV and recover without restarting.
- Upload the golden CSV twice and confirm deterministic results.
- Verify labels and units on every chart.
- Verify the synthetic-data badge.
- Save logs from the successful run.
- Copy the complete package to a second laptop and USB drive.

## Five minutes before presenting

- Connect power and disable sleep/notifications.
- Close development servers and unrelated apps.
- Run preflight.
- Start production mode, not Vite development mode.
- Check `/ready` and the UI model version.
- Open the verified CSV folder.
- Use the rehearsed browser zoom.

## Live sequence

1. Show the ready model/version indicator.
2. Upload the CSV visibly.
3. Let the real endpoint validate and score it.
4. Explain action counts, not a generic accuracy number.
5. Select the known early-drift component.
6. Show that it remains below the fixed limit.
7. Show batch-relative evidence.
8. Show the 168-hour prediction and interval.
9. Read the recommendation and reasons.
10. State that an engineer makes the final decision.

## Honest fallback ladder

1. Restart the same local production process.
2. Run the same CSV through the CLI and same domain service.
3. Upload the CSV through FastAPI's local API documentation.
4. Show the last signed preflight report only as evidence of prior verification,
   explicitly saying the live UI failed.

Never switch to hard-coded results or call a screenshot live inference.

