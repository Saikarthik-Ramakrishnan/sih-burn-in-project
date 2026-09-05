import PredictionDashboard from "./components/PredictionDashboard.jsx";
import demoResponse from "./data/demoResponse.json";
import "./App.css";

function App() {
  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">MLCC leakage prediction</p>
          <h1>Batch health dashboard</h1>
        </div>
        <div className="status-pill">Demo response loaded</div>
      </header>

      <PredictionDashboard
        predictionResponse={demoResponse}
        LeakageChart={LeakageChart}
      />
    </main>
  );
}

function LeakageChart({ data }) {
  return (
    <section className="chart-grid" aria-label="Leakage forecast charts">
      {data.map((series) => (
        <article className="chart-card" key={series.componentId}>
          <h2>{series.componentId}</h2>
          <div className="chart-points">
            {series.points.map((point, index) => (
              <div className={`chart-point ${point.kind}`} key={`${point.kind}-${point.time}-${index}`}>
                <span className="point-kind">{point.kind}</span>
                <span>{point.time === null ? "N/A" : `${point.time} ${point.timeUnit}`}</span>
                <strong>{point.value === null ? `N/A ${point.unit}` : `${point.value} ${point.unit}`}</strong>
                {point.kind === "predicted" ? (
                  <small>
                    Interval: {point.intervalLower === null || point.intervalUpper === null
                      ? `N/A ${point.intervalUnit}`
                      : `${point.intervalLower}-${point.intervalUpper} ${point.intervalUnit}`}
                  </small>
                ) : null}
              </div>
            ))}
          </div>
        </article>
      ))}
    </section>
  );
}

export default App;
