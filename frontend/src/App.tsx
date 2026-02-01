/**
 * App Component
 * 
 * Main application component handling view routing:
 * Upload → Analyzing → Dashboard
 */

import { useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import type { DashboardResponse, AppView } from './types';
import { Upload } from './components/Upload';
import { Dashboard } from './components/Dashboard';
import { uploadAndAnalyze, loadSampleAndAnalyze } from './api/client';

function App() {
  // Application state
  const [view, setView] = useState<AppView>('upload');
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState<string>('');

  // Handle file upload
  const handleFileUpload = useCallback(async (file: File) => {
    console.log('[App] Starting file upload:', file.name);
    setIsLoading(true);
    setError(null);
    setView('analyzing');

    try {
      const data = await uploadAndAnalyze(file, (step) => {
        console.log('[App] Progress:', step);
        setLoadingStep(step);
      });
      console.log('[App] Upload complete, dashboard data:', data);
      setDashboardData(data);
      setView('dashboard');
    } catch (err) {
      console.error('[App] Upload error:', err);
      const errorMessage = err instanceof Error 
        ? (err as { details?: string }).details || err.message 
        : 'Failed to analyze file';
      setError(errorMessage);
      setView('upload');
    } finally {
      setIsLoading(false);
      setLoadingStep('');
    }
  }, []);

  // Handle sample data
  const handleUseSampleData = useCallback(async () => {
    console.log('[App] Loading sample data...');
    setIsLoading(true);
    setError(null);
    setView('analyzing');

    try {
      const data = await loadSampleAndAnalyze((step) => {
        console.log('[App] Progress:', step);
        setLoadingStep(step);
      });
      console.log('[App] Sample data loaded, dashboard data:', data);
      setDashboardData(data);
      setView('dashboard');
    } catch (err) {
      console.error('[App] Sample data error:', err);
      const errorMessage = err instanceof Error 
        ? (err as { details?: string }).details || err.message 
        : 'Failed to load sample data';
      setError(errorMessage);
      setView('upload');
    } finally {
      setIsLoading(false);
      setLoadingStep('');
    }
  }, []);

  // Reset to upload view
  const handleReset = useCallback(() => {
    setView('upload');
    setDashboardData(null);
    setError(null);
  }, []);

  // Render based on current view
  switch (view) {
    case 'upload':
      return (
        <Upload
          onFileUpload={handleFileUpload}
          onUseSampleData={handleUseSampleData}
          isLoading={isLoading}
          error={error}
        />
      );

    case 'analyzing':
      return <AnalyzingView step={loadingStep} />;

    case 'dashboard':
      if (!dashboardData) {
        return <AnalyzingView step="Loading dashboard..." />;
      }
      return <Dashboard data={dashboardData} onReset={handleReset} />;

    default:
      return null;
  }
}

// =============================================================================
// Analyzing View (Loading State)
// =============================================================================

interface AnalyzingViewProps {
  step: string;
}

function AnalyzingView({ step }: AnalyzingViewProps) {
  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="text-center">
        {/* Spinner */}
        <div className="flex justify-center mb-5">
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
        </div>

        {/* Title */}
        <h2 className="text-base font-semibold text-textPrimary mb-1">
          Analyzing Your Finances
        </h2>

        {/* Step indicator */}
        <p className="text-sm text-muted mb-6">
          {step || 'Processing transactions...'}
        </p>

        {/* Steps list */}
        <div className="max-w-xs mx-auto space-y-2 text-left">
          <StepItem 
            label="Categorizing transactions" 
            isActive={step.includes('Analyzing')}
          />
          <StepItem 
            label="Detecting anomalies" 
            isActive={step.includes('Analyzing')}
          />
          <StepItem 
            label="Finding recurring charges" 
            isActive={step.includes('Analyzing')}
          />
          <StepItem 
            label="Generating insights" 
            isActive={step.includes('Analyzing')}
          />
        </div>
      </div>
    </div>
  );
}

// Step item component
function StepItem({ label, isActive }: { label: string; isActive: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div 
        className={`w-1.5 h-1.5 rounded-full ${
          isActive ? 'bg-accent' : 'bg-border'
        }`}
      />
      <span className={`text-sm ${
        isActive ? 'text-textPrimary' : 'text-muted'
      }`}>
        {label}
      </span>
    </div>
  );
}

export default App;
