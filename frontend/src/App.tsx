import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Footer } from './components/Footer';

// V1 Core Retained Pages
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { MedicalProfilePage } from './pages/MedicalProfilePage';
import { UploadReportPage } from './pages/UploadReportPage';
import { ReportAnalysisPage } from './pages/ReportAnalysisPage';
import { MedicalRecordsPage } from './pages/MedicalRecordsPage';
import { HospitalFinderPage } from './pages/HospitalFinderPage';
import { HospitalDetailsPage } from './pages/HospitalDetailsPage';
import { HospitalComparisonPage } from './pages/HospitalComparisonPage';
import { CostEstimatorPage } from './pages/CostEstimatorPage';
import { MedicalTravelPage } from './pages/MedicalTravelPage';
import { AiAssistantPage } from './pages/AiAssistantPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';

export const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        
        {/* Global Top Navbar */}
        <Navbar />

        {/* Main Body Layout */}
        <div className="flex-1 flex max-w-[1600px] w-full mx-auto">
          {/* Sidebar */}
          <Sidebar />

          {/* Page Main Content Area */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 min-w-0">
            <Routes>
              {/* Decision Support Pipeline Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/profile" element={<MedicalProfilePage />} />
              <Route path="/reports/upload" element={<UploadReportPage />} />
              <Route path="/reports/:id/analysis" element={<ReportAnalysisPage />} />
              <Route path="/analysis" element={<ReportAnalysisPage />} />
              <Route path="/records" element={<MedicalRecordsPage />} />
              <Route path="/hospitals" element={<HospitalFinderPage />} />
              <Route path="/hospitals/compare" element={<HospitalComparisonPage />} />
              <Route path="/hospitals/:id" element={<HospitalDetailsPage />} />
              <Route path="/doctors" element={<Navigate to="/hospitals" replace />} />
              <Route path="/cost" element={<CostEstimatorPage />} />
              <Route path="/travel" element={<MedicalTravelPage />} />
              <Route path="/assistant" element={<AiAssistantPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/settings" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>

        {/* Global Footer */}
        <Footer />

      </div>
    </Router>
  );
};

export default App;
