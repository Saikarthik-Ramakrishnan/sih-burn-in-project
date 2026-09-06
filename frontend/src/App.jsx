import React, { useState, useEffect } from 'react';
import AmbientBackdrop from './components/layout/AmbientBackdrop';
import Header from './components/layout/Header';
import Navigation from './components/layout/Navigation';
import OverviewView from './components/views/OverviewView';
import ComponentGridView from './components/views/ComponentGridView';
import TopologyView from './components/views/TopologyView';
import ComponentDetailView from './components/views/ComponentDetailView';
import ChamberView from './components/views/ChamberView';
import ExportView from './components/views/ExportView';
import UploadModal from './components/upload/UploadModal';
import DEMO_DATASET from './lib/demoData';
import { checkHealth } from './lib/api';

export default function App() {
  const [dataset, setDataset] = useState(DEMO_DATASET);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedComponentId, setSelectedComponentId] = useState(
    DEMO_DATASET?.records?.[0]?.component_id || ''
  );
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [backendReady, setBackendReady] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Probe backend liveness and readiness on startup
  useEffect(() => {
    let isMounted = true;
    const probe = async () => {
      try {
        const res = await checkHealth();
        if (isMounted) {
          setBackendReady(Boolean(res.ok && res.data?.ready));
        }
      } catch {
        if (isMounted) setBackendReady(false);
      }
    };
    probe();
    const interval = setInterval(probe, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleFilterByDecision = (filterKey) => {
    setActiveFilter(filterKey);
    setActiveTab('components');
  };

  const handleInspectComponent = (id) => {
    setSelectedComponentId(id);
    setActiveTab('inspector');
  };

  const handleUploadSuccess = (newResponse) => {
    // Normalize or use backend response
    if (newResponse && newResponse.records) {
      // If records don't have board_positions, ensure they are indexed
      const enrichedRecords = newResponse.records.map((r, i) => ({
        ...r,
        context: {
          ...r.context,
          board_position: r.context?.board_position || (i + 1),
          tester_channel: r.context?.tester_channel || ((i % 16) + 1)
        },
        within_limit_but_unusual: r.within_limit_but_unusual ?? (r.limits?.applicable_limit && r.latest_value < r.limits.applicable_limit && r.anomaly?.is_anomaly)
      }));

      const unusualCount = enrichedRecords.filter(r => r.within_limit_but_unusual).length;

      setDataset({
        ...newResponse,
        records: enrichedRecords,
        within_limits_but_unusual_count: unusualCount
      });

      if (enrichedRecords.length > 0) {
        setSelectedComponentId(enrichedRecords[0].component_id);
      }
    }
    setActiveTab('overview');
  };

  const handleReloadDemo = () => {
    setDataset(DEMO_DATASET);
    setSelectedComponentId(DEMO_DATASET.records[0].component_id);
    setActiveFilter('ALL');
  };

  const counts = {
    total: dataset?.records?.length || 0,
    anomalies: dataset?.records?.filter(r => r.anomaly?.is_anomaly).length || 0
  };

  return (
    <div className="min-h-screen relative flex font-sans selection:bg-orange-500 selection:text-black">
      {/* 1. Squircle Thermal Background */}
      <AmbientBackdrop />

      {/* 2. Hover-Expanding Left Sidebar Navigation */}
      <Navigation
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        counts={counts}
        onOpenUpload={() => setIsUploadOpen(true)}
        backendReady={backendReady}
      />

      {/* 3. Main Content Viewport (offset by 64px for collapsed sidebar) */}
      <div className="flex-1 flex flex-col min-w-0 pl-16">
        {/* Top Header */}
        <Header
          backendReady={backendReady}
          dataset={dataset}
          onOpenUpload={() => setIsUploadOpen(true)}
          onReloadDemo={handleReloadDemo}
          isSubmitting={isSubmitting}
        />

        {/* Active Viewport Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-6 pt-6 pb-16">
          {activeTab === 'overview' && (
            <OverviewView
              dataset={dataset}
              onFilterByDecision={handleFilterByDecision}
              onInspectComponent={handleInspectComponent}
              onNavigateToComponents={() => setActiveTab('components')}
            />
          )}

          {activeTab === 'components' && (
            <ComponentGridView
              dataset={dataset}
              selectedComponentId={selectedComponentId}
              setSelectedComponentId={setSelectedComponentId}
              onInspectComponent={handleInspectComponent}
              activeFilter={activeFilter}
              setActiveFilter={setActiveFilter}
            />
          )}

          {activeTab === 'topology' && (
            <TopologyView
              dataset={dataset}
              selectedComponentId={selectedComponentId}
              setSelectedComponentId={setSelectedComponentId}
              onInspectComponent={handleInspectComponent}
            />
          )}

          {activeTab === 'inspector' && (
            <ComponentDetailView
              dataset={dataset}
              selectedComponentId={selectedComponentId}
              setSelectedComponentId={setSelectedComponentId}
            />
          )}

          {activeTab === 'chamber' && (
            <ChamberView dataset={dataset} />
          )}

          {activeTab === 'export' && (
            <ExportView dataset={dataset} />
          )}
        </main>

        {/* Footer */}
        <footer className="w-full border-t border-white/[0.05] bg-[#07080d]/80 backdrop-blur-md py-4 px-6 text-center text-xs font-mono text-slate-500">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>
              SIH26170 · Component Burn-In Early Anomaly &amp; Forecasting Intelligence
            </span>
            <span className="text-slate-400">
              Engineered for Industrial Electronic Qualification
            </span>
          </div>
        </footer>
      </div>

      {/* Upload Ingestion Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
        onLoadSample={handleReloadDemo}
      />
    </div>
  );
}
