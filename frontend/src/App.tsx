import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { EmergencyBanner } from './components/EmergencyBanner';
import { Footer } from './components/Footer';

// All 25 Required User Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { MedicalProfilePage } from './pages/MedicalProfilePage';
import { UploadReportPage } from './pages/UploadReportPage';
import { ReportAnalysisPage } from './pages/ReportAnalysisPage';
import { AiAssistantPage } from './pages/AiAssistantPage';
import { HospitalFinderPage } from './pages/HospitalFinderPage';
import { HospitalDetailsPage } from './pages/HospitalDetailsPage';
import { HospitalComparisonPage } from './pages/HospitalComparisonPage';
import { DoctorRecommendationsPage } from './pages/DoctorRecommendationsPage';
import { AppointmentBookingPage } from './pages/AppointmentBookingPage';
import { PharmacyFinderPage } from './pages/PharmacyFinderPage';
import { SymptomGuidancePage } from './pages/SymptomGuidancePage';
import { InsuranceHelpPage } from './pages/InsuranceHelpPage';
import { MedicalTranslationPage } from './pages/MedicalTranslationPage';
import { AccommodationPage } from './pages/AccommodationPage';
import { NavigationPage } from './pages/NavigationPage';
import { TravelPlannerPage } from './pages/TravelPlannerPage';
import { LocalHealthPage } from './pages/LocalHealthPage';
import { EmergencyAssistancePage } from './pages/EmergencyAssistancePage';
import { EmergencyContactsPage } from './pages/EmergencyContactsPage';
import { MedicalRecordsPage } from './pages/MedicalRecordsPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        
        {/* Sticky Emergency Quick Access Bar */}
        <EmergencyBanner />

        {/* Global Top Navbar */}
        <Navbar />

        {/* Main Body Layout */}
        <div className="flex-1 flex max-w-[1600px] w-full mx-auto">
          {/* Sidebar */}
          <Sidebar />

          {/* Page Main Content Area */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 min-w-0">
            <Routes>
              {/* All 25 Required Page Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/profile" element={<MedicalProfilePage />} />
              <Route path="/reports/upload" element={<UploadReportPage />} />
              <Route path="/reports/:id/analysis" element={<ReportAnalysisPage />} />
              <Route path="/assistant" element={<AiAssistantPage />} />
              <Route path="/hospitals" element={<HospitalFinderPage />} />
              <Route path="/hospitals/compare" element={<HospitalComparisonPage />} />
              <Route path="/hospitals/:id" element={<HospitalDetailsPage />} />
              <Route path="/doctors" element={<DoctorRecommendationsPage />} />
              <Route path="/appointments/book" element={<AppointmentBookingPage />} />
              <Route path="/pharmacies" element={<PharmacyFinderPage />} />
              <Route path="/symptoms" element={<SymptomGuidancePage />} />
              <Route path="/insurance" element={<InsuranceHelpPage />} />
              <Route path="/translate" element={<MedicalTranslationPage />} />
              <Route path="/accommodation" element={<AccommodationPage />} />
              <Route path="/navigation" element={<NavigationPage />} />
              <Route path="/travel-planner" element={<TravelPlannerPage />} />
              <Route path="/local-health" element={<LocalHealthPage />} />
              <Route path="/emergency" element={<EmergencyAssistancePage />} />
              <Route path="/emergency-contacts" element={<EmergencyContactsPage />} />
              <Route path="/records" element={<MedicalRecordsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
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
