// API Client & Service Layer for AI Based Decision Support System (V1 Core)

const BASE_URL = '/api';

// ==========================================
// Types & Data Contracts
// ==========================================

export interface UserSession {
  id: number;
  email: string;
  full_name: string;
  role: string;
  specialty?: string;
  username?: string;
}

export interface DemoUserOption {
  id: number;
  username: string;
  email: string;
  full_name: string;
  specialty: string;
  clinical_focus: string;
  city: string;
  badge: string;
}

export interface PatientProfile {
  id?: number;
  user_id?: number;
  age: number;
  gender: string;
  blood_group: string;
  allergies: string;
  chronic_conditions: string;
  current_city: string;
  preferred_currency?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  // Phase 3 Persistent Clinical Profile Fields
  conditions?: string[];
  symptoms?: string[];
  tests?: string[];
  test_results?: TestResultItem[];
  medications?: string[];
  procedures?: string[];
  medical_history?: string[];
  last_report_id?: number;
  structured_data?: StructuredClinicalInfo;
}

export interface ExtractedEntity {
  id?: number;
  entity_type: string;
  entity_name: string;
  confidence: number;
  context_snippet?: string;
}

export interface DocumentMetadata {
  patient_name?: string;
  patient_id?: string;
  report_date?: string;
}

export interface PatientDemographics {
  age?: number;
  gender?: string;
}

export interface TestResultItem {
  test_name: string;
  value: string;
  unit?: string;
  reference_range?: string;
  status?: string;
}

export interface StructuredClinicalInfo {
  metadata: DocumentMetadata;
  demographics: PatientDemographics;
  conditions: string[];
  symptoms: string[];
  tests: string[];
  test_results: TestResultItem[];
  medications: string[];
  procedures: string[];
  medical_history: string[];
}

export interface MedicalReport {
  id: number;
  user_id?: number;
  filename: string;
  file_path: string;
  status: string;
  ocr_text?: string;
  summary?: string;
  recommended_specialty: string;
  important_notes?: string;
  grounding_notes?: string;
  grounding_sources?: Array<{
    title: string;
    organization: string;
    source_reference: string;
    reference_url?: string;
    score?: number;
  }>;
  created_at: string;
  entities: ExtractedEntity[];
  structured_info?: StructuredClinicalInfo;
}

export interface Hospital {
  id: number;
  name: string;
  city: string;
  state: string;
  address: string;
  lat: number;
  lng: number;
  specialties: string[];
  rating: number;
  distance_km: number;
  insurance_accepted: string[];
  facilities: string[];
  contact_phone: string;
  availability_status: string;
  cost_tier?: string;
  quality_rating?: number;
  accreditation?: string;
  treatment_capabilities?: string[];
  icu_beds?: number;
  emergency_24x7?: boolean;
  estimated_cost_tier?: number;
  recommendation_score?: number;
  shap_reasons?: string[];
  reasons?: string[];
  score_breakdown?: Record<string, number>;
  provenance?: any;
}

export interface Doctor {
  id: number;
  hospital_id: number;
  name: string;
  specialty: string;
  experience_years: number;
  qualification: string;
  rating: number;
  consultation_fee: number;
  availability_days: string;
  expertise?: string[];
  match_score?: number;
  score_breakdown?: Record<string, number>;
  reasons?: string[];
  hospital_name?: string;
  hospital_city?: string;
  provenance?: any;
}

export interface PatientPreferences {
  preferred_city?: string;
  user_location?: { lat: number; lng: number };
  max_distance_km?: number;
  insurance_provider?: string;
  max_budget_inr?: number;
  max_cost_tier?: string;
  preferred_languages?: string[];
  priority_mode?: 'balanced' | 'cost_sensitive' | 'quality_focused' | 'proximity_focused';
  min_hospital_rating?: number;
  require_nabh_jci?: boolean;
  treatment_type_interest?: string;
}

export interface EligibilityAuditItem {
  provider_id: number;
  name: string;
  entity_type: string;
  eligible: boolean;
  exclusion_reasons: string[];
}

export interface PersonalizedRecommendationResponse {
  clinical_profile_summary: Record<string, any>;
  active_weights: Record<string, number>;
  priority_mode: string;
  hospitals: Hospital[];
  doctors: Doctor[];
  treatment_pathways: TreatmentPathway[];
  eligibility_audit: EligibilityAuditItem[];
  synthetic_benchmark_notice: string;
}

export interface TreatmentPathway {
  pathway_name: string;
  specialty: string;
  condition: string;
  description: string;
  suitability: string;
  estimated_duration_days: number;
  flight_clearance_guideline: string;
  grounding_sources: {
    organization: string;
    title: string;
    reference_url: string;
  }[];
  clinical_disclaimer: string;
  allergy_conflict_detected?: boolean;
  allergy_warning?: string;
}

export interface TreatmentRecommendationResponse {
  patient_condition: string;
  specialty: string;
  recommended_pathways: TreatmentPathway[];
  clinical_notes: string;
  patient_context_applied?: {
    user_id?: number;
    allergies_evaluated?: string[];
    conditions_evaluated?: string[];
  };
  sources_consulted: {
    title: string;
    organization: string;
    reference_url: string;
  }[];
}

export interface CostPredictionRequest {
  treatment_name: string;
  city?: string;
  room_type?: string;
  duration_days?: number;
  user_id?: number;
  report_id?: number;
  hospital_id?: number;
  age?: number;
  gender?: string;
  specialty?: string;
  comorbidity_count?: number;
  has_diabetes?: boolean;
  has_hypertension?: boolean;
  has_cardiac_history?: boolean;
  hospital_tier?: string;
  insurance_type?: string;
}

export interface CostPredictionResponse {
  treatment_name: string;
  canonical_treatment?: string;
  city: string;
  room_type: string;
  duration_days: number;
  predicted_los_days?: number;
  los_source?: string;
  estimated_min_cost: number;
  estimated_max_cost: number;
  estimated_avg_cost: number;
  currency: string;
  empirical_model_error_range?: {
    lower_bound: number;
    upper_bound: number;
    held_out_rmse_inr: number;
    formula: string;
    description: string;
  };
  shap_feature_impacts: Record<string, number>;
  base_value?: number;
  additive_difference?: number;
  relative_additive_difference?: number;
  disclaimer: string;
}

export interface CostExplanationResponse {
  prediction: CostPredictionResponse;
  shap_explanation: {
    title: string;
    estimated_avg: number;
    base_value?: number;
    additive_property_verified?: boolean;
    breakdown: Array<{
      feature: string;
      val_inr: number;
      formatted: string;
      positive: boolean;
    }>;
    empirical_model_error_range?: {
      lower_bound: number;
      upper_bound: number;
      held_out_rmse_inr: number;
      formula: string;
      description: string;
    };
    summary_note: string;
  };
}

export interface RecoveryMilestone {
  phase: string;
  title: string;
  timeline_days: string;
  clinical_focus: string;
  guideline_statement: string;
  clearance_status: string;
}

export interface ClinicalRecoveryTimelineResponse {
  treatment_name: string;
  specialty: string;
  predicted_los_days: number;
  total_recovery_window_days: number;
  milestones: RecoveryMilestone[];
  clinical_guideline_sources: string[];
  safety_disclaimer: string;
}

export interface ModelMetricsResponse {
  cost_model: {
    model_type: string;
    n_estimators: number;
    max_depth: number;
    learning_rate: number;
    mae_inr: number;
    rmse_inr: number;
    r2_score: number;
    input_features: string[];
  };
  los_model: {
    model_type: string;
    n_estimators: number;
    max_depth: number;
    learning_rate: number;
    mae_days: number;
    rmse_days: number;
    r2_score: number;
    input_features: string[];
  };
  training_dataset: {
    data_source: string;
    is_benchmark: boolean;
    sample_size: number;
    provenance_notes: string;
  };
  split: {
    train_samples: number;
    val_samples: number;
    test_samples: number;
    random_seed: number;
  };
}

export interface ChatResponse {
  reply: string;
  conversation_id: number;
  citations: string[];
  grounding_status?: string;
  retrieved_evidence?: Array<{
    title: string;
    organization: string;
    source_reference: string;
    reference_url?: string;
    score?: number;
  }>;
  disclaimer: string;
  is_emergency?: boolean;
  emergency_alert?: string;
  patient_context_applied?: {
    age?: number;
    gender?: string;
    allergies?: string[];
    chronic_conditions?: string[];
    medical_history?: string[];
    report_id?: number;
    report_summary?: string;
    specialty?: string;
    entities?: string[];
    hospital_name?: string;
    hospital_city?: string;
  };
  suggested_followups?: string[];
  safety_guardrails_triggered?: string[];
  llm_provider?: string;
  model_used?: string;
}

// ==========================================
// Synthetic Demo Session & Authentication
// ==========================================

export const SYNTHETIC_DEMO_USERS: DemoUserOption[] = [
  {
    id: 1,
    username: 'demo_cardio',
    email: 'patient@example.com',
    full_name: 'Rahul Verma',
    specialty: 'Cardiology',
    clinical_focus: 'Coronary Artery Disease (CAD)',
    city: 'Hyderabad',
    badge: 'Synthetic Demo Patient 1'
  },
  {
    id: 2,
    username: 'demo_neuro',
    email: 'patient2@example.com',
    full_name: 'Priya Sharma',
    specialty: 'Neurology',
    clinical_focus: 'Chronic Migraine & Neuralgia',
    city: 'Bengaluru',
    badge: 'Synthetic Demo Patient 2'
  },
  {
    id: 3,
    username: 'demo_ortho',
    email: 'patient3@example.com',
    full_name: 'Amit Patel',
    specialty: 'Orthopedics',
    clinical_focus: 'Bilateral Knee Osteoarthritis',
    city: 'Delhi',
    badge: 'Synthetic Demo Patient 3'
  }
];

const DEFAULT_DEMO_USER: UserSession = {
  id: 1,
  email: 'patient@example.com',
  full_name: 'Rahul Verma',
  role: 'patient',
  specialty: 'Cardiology',
  username: 'demo_cardio'
};

export function getCurrentUser(): UserSession {
  try {
    const raw = localStorage.getItem('currentUser');
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (e) {
    // ignore
  }
  return DEFAULT_DEMO_USER;
}

export function getCurrentUserId(): number {
  return getCurrentUser().id;
}

export function isAuthenticated(): boolean {
  try {
    return localStorage.getItem('currentUser') !== null;
  } catch {
    return false;
  }
}

export function getActiveReportId(): number | null {
  try {
    const raw = sessionStorage.getItem('active_report_id');
    return raw ? Number(raw) : null;
  } catch {
    return null;
  }
}

export function setActiveReportId(reportId: number | null | undefined) {
  try {
    if (reportId) {
      sessionStorage.setItem('active_report_id', String(reportId));
    } else {
      sessionStorage.removeItem('active_report_id');
    }
  } catch {
    // ignore
  }
}

export function clearActiveReportId() {
  try {
    sessionStorage.removeItem('active_report_id');
  } catch {
    // ignore
  }
}

export function setCurrentUser(user: UserSession) {
  try {
    const prevRaw = localStorage.getItem('currentUser');
    if (prevRaw) {
      const prev = JSON.parse(prevRaw);
      if (prev.id !== user.id) {
        clearActiveReportId();
      }
    } else {
      clearActiveReportId();
    }
  } catch {
    clearActiveReportId();
  }
  localStorage.setItem('currentUser', JSON.stringify(user));
}

export function clearCurrentUser() {
  localStorage.removeItem('currentUser');
  localStorage.removeItem('user_token');
  clearActiveReportId();
}

export async function loginApi(username: string, password: string): Promise<{ access_token: string; user: UserSession }> {
  // Always clear previous user's active report on login
  clearActiveReportId();

  const data = await fetchApi<{ access_token: string; user: UserSession }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  if (data && data.user) {
    setCurrentUser(data.user);
    if (data.access_token) {
      localStorage.setItem('user_token', data.access_token);
    }
    // Proactively resolve and set this user's latest seeded report
    try {
      const reports = await getUserReports(data.user.id);
      if (reports && reports.length > 0) {
        setActiveReportId(reports[0].id);
      }
    } catch {
      // ignore
    }
  }
  return data;
}

export async function logoutApi(): Promise<{ message: string }> {
  try {
    const userId = getCurrentUserId();
    await fetchApi<{ message: string }>(`/auth/logout?user_id=${userId}`, {
      method: 'POST',
    });
  } catch {
    // ignore
  } finally {
    clearCurrentUser();
  }
  return { message: 'Logged out successfully' };
}

export async function getDemoUsersApi(): Promise<DemoUserOption[]> {
  try {
    return await fetchApi<DemoUserOption[]>('/auth/demo-users');
  } catch {
    return SYNTHETIC_DEMO_USERS;
  }
}

// ==========================================
// Core Fetch Wrapper
// ==========================================

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('user_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'API Error' }));
    throw new Error(errData.detail || `HTTP Error ${res.status}`);
  }
  return await res.json();
}

// ==========================================
// Clinical Profile Service (auth.py profile endpoints)
// ==========================================

export async function getProfile(userId = getCurrentUserId()): Promise<PatientProfile> {
  return await fetchApi<PatientProfile>(`/auth/profile?user_id=${userId}`);
}

export async function updateProfile(profileData: Partial<PatientProfile>, userId = getCurrentUserId()): Promise<PatientProfile> {
  return await fetchApi<PatientProfile>(`/auth/profile?user_id=${userId}`, {
    method: 'PUT',
    body: JSON.stringify(profileData),
  });
}

export async function syncProfileFromReport(reportId: number, userId = getCurrentUserId()): Promise<PatientProfile> {
  return await fetchApi<PatientProfile>(`/auth/profile/sync-from-report/${reportId}?user_id=${userId}`, {
    method: 'POST',
  });
}

export async function getSharedClinicalContext(userId = getCurrentUserId()): Promise<any> {
  return await fetchApi<any>(`/auth/profile/shared-context?user_id=${userId}`);
}

export const getPatientProfile = getProfile;

// ==========================================
// Reports & OCR Service
// ==========================================

export async function uploadReportApi(file: File, userId = getCurrentUserId()): Promise<MedicalReport> {
  const formData = new FormData();
  formData.append('file', file);

  const headers: Record<string, string> = {};
  const token = localStorage.getItem('user_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}/reports/upload?user_id=${userId}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Report upload failed');
  }
  return await res.json();
}

export async function getUserReports(userId = getCurrentUserId()): Promise<MedicalReport[]> {
  return await fetchApi<MedicalReport[]>(`/reports/?user_id=${userId}`);
}

export async function getReportById(reportId: number | string): Promise<MedicalReport> {
  return await fetchApi<MedicalReport>(`/reports/${reportId}`);
}

export async function getLatestReport(userId = getCurrentUserId()): Promise<MedicalReport | null> {
  try {
    const reports = await getUserReports(userId);
    return reports && reports.length > 0 ? reports[0] : null;
  } catch {
    return null;
  }
}

export async function getOrResolveActiveReport(userId = getCurrentUserId()): Promise<MedicalReport | null> {
  const activeId = getActiveReportId();
  if (activeId) {
    try {
      const rep = await getReportById(activeId);
      if (rep && (rep.user_id === userId || !rep.user_id)) {
        return rep;
      } else {
        clearActiveReportId();
      }
    } catch {
      // Stale or foreign report ID
      clearActiveReportId();
    }
  }

  // Fallback: look up latest report for this authenticated user
  try {
    const reports = await getUserReports(userId);
    if (reports && reports.length > 0) {
      const latest = reports[0];
      setActiveReportId(latest.id);
      return latest;
    }
  } catch {
    // No reports found
  }
  clearActiveReportId();
  return null;
}

// ==========================================
// Recommendations Service
// ==========================================

export async function getRecommendedHospitals(params: {
  specialty?: string;
  city?: string;
  max_budget?: number;
  insurance?: string;
  priority_mode?: string;
  user_id?: number;
  report_id?: number;
} = {}): Promise<Hospital[]> {
  const query = new URLSearchParams();
  if (params.specialty) query.set('specialty', params.specialty);
  if (params.city) query.set('city', params.city);
  if (params.max_budget) query.set('max_budget', params.max_budget.toString());
  if (params.insurance) query.set('insurance', params.insurance);
  if (params.priority_mode) query.set('priority_mode', params.priority_mode);
  if (params.user_id) query.set('user_id', params.user_id.toString());
  if (params.report_id) query.set('report_id', params.report_id.toString());

  return await fetchApi<Hospital[]>(`/recommend/hospitals?${query.toString()}`);
}

export async function getPersonalizedRecommendations(params: {
  user_id?: number;
  clinical_profile?: Record<string, any>;
  preferences?: PatientPreferences;
  top_hospitals?: number;
  top_doctors?: number;
  top_pathways?: number;
}): Promise<PersonalizedRecommendationResponse> {
  return await fetchApi<PersonalizedRecommendationResponse>('/recommend/personalized', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getHospitalById(id: number | string): Promise<Hospital> {
  return await fetchApi<Hospital>(`/recommend/hospitals/${id}`);
}

export async function getRecommendedDoctors(params: {
  specialty?: string;
  hospital_id?: number;
  city?: string;
  user_id?: number;
  report_id?: number;
} = {}): Promise<Doctor[]> {
  const query = new URLSearchParams();
  if (params.specialty) query.set('specialty', params.specialty);
  if (params.hospital_id) query.set('hospital_id', params.hospital_id.toString());
  if (params.city) query.set('city', params.city);
  if (params.user_id) query.set('user_id', params.user_id.toString());
  if (params.report_id) query.set('report_id', params.report_id.toString());

  return await fetchApi<Doctor[]>(`/recommend/doctors?${query.toString()}`);
}

export async function getRecommendedTreatments(params: {
  condition?: string;
  specialty?: string;
  report_id?: number;
  user_id?: number;
} = {}): Promise<TreatmentRecommendationResponse> {
  const query = new URLSearchParams();
  if (params.condition) query.set('condition', params.condition);
  if (params.specialty) query.set('specialty', params.specialty);
  if (params.report_id) query.set('report_id', params.report_id.toString());
  if (params.user_id) query.set('user_id', params.user_id.toString());

  return await fetchApi<TreatmentRecommendationResponse>(`/recommend/treatments?${query.toString()}`);
}

export async function compareHospitals(hospitalIds: number[], params?: {
  user_id?: number;
  city?: string;
  specialty?: string;
  priority_mode?: string;
  max_budget?: number;
  insurance?: string;
  report_id?: number;
}): Promise<{
  compared_hospitals: Hospital[];
  ai_recommendation: string;
}> {
  const query = new URLSearchParams();
  if (params?.user_id) query.append('user_id', String(params.user_id));
  if (params?.city) query.append('city', params.city);
  if (params?.specialty) query.append('specialty', params.specialty);
  if (params?.priority_mode) query.append('priority_mode', params.priority_mode);
  if (params?.max_budget) query.append('max_budget', String(params.max_budget));
  if (params?.insurance) query.append('insurance', params.insurance);
  if (params?.report_id) query.append('report_id', String(params.report_id));
  const qStr = query.toString() ? `?${query.toString()}` : '';
  return await fetchApi<{
    compared_hospitals: Hospital[];
    ai_recommendation: string;
  }>(`/recommend/compare${qStr}`, {
    method: 'POST',
    body: JSON.stringify(hospitalIds),
  });
}

export async function compareDoctors(doctorIds: number[], params?: {
  user_id?: number;
  specialty?: string;
  report_id?: number;
}): Promise<{
  compared_doctors: Doctor[];
  ai_recommendation: string;
}> {
  const query = new URLSearchParams();
  if (params?.user_id) query.append('user_id', String(params.user_id));
  if (params?.specialty) query.append('specialty', params.specialty);
  if (params?.report_id) query.append('report_id', String(params.report_id));
  const qStr = query.toString() ? `?${query.toString()}` : '';
  return await fetchApi<{
    compared_doctors: Doctor[];
    ai_recommendation: string;
  }>(`/recommend/compare-doctors${qStr}`, {
    method: 'POST',
    body: JSON.stringify(doctorIds),
  });
}

// ==========================================
// Treatment Cost & SHAP Service
// ==========================================

export async function predictTreatmentCost(req: CostPredictionRequest): Promise<CostPredictionResponse> {
  return await fetchApi<CostPredictionResponse>('/cost/predict', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function explainTreatmentCost(req: CostPredictionRequest): Promise<CostExplanationResponse> {
  return await fetchApi<CostExplanationResponse>('/cost/explain', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function getClinicalRecoveryTimeline(req: CostPredictionRequest): Promise<ClinicalRecoveryTimelineResponse> {
  return await fetchApi<ClinicalRecoveryTimelineResponse>('/cost/recovery-timeline', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function getCostModelMetrics(): Promise<ModelMetricsResponse> {
  return await fetchApi<ModelMetricsResponse>('/cost/metrics');
}

// ==========================================
// Contextual AI Healthcare Assistant Service
// ==========================================

export async function sendAssistantChat(
  message: string,
  conversation_id?: number,
  report_id?: number,
  hospital_id?: number,
  userId = getCurrentUserId()
): Promise<ChatResponse> {
  const query = new URLSearchParams({ user_id: String(userId) });
  if (report_id) {
    query.set('report_id', String(report_id));
  }
  return await fetchApi<ChatResponse>(`/services/chat?${query.toString()}`, {
    method: 'POST',
    body: JSON.stringify({ message, conversation_id, report_id, hospital_id }),
  });
}

export async function getChatHistory(conversationId?: number, userId = getCurrentUserId()): Promise<any> {
  const query = new URLSearchParams({ user_id: String(userId) });
  if (conversationId) {
    query.set('conversation_id', String(conversationId));
  }
  return await fetchApi<any>(`/services/chat/history?${query.toString()}`);
}

// ==========================================
// Medical Travel System (Free & Open-Source)
// ==========================================

export interface OpenRouteWaypoint {
  name: string;
  lat: number;
  lon: number;
}

export interface OpenRouteRequest {
  origin: string;
  destination: string;
  travel_mode: 'car' | 'two_wheeler' | 'walking' | 'bicycle' | 'transit';
}

export interface OpenRouteResponse {
  origin: OpenRouteWaypoint;
  destination: OpenRouteWaypoint;
  travel_mode: string;
  distance_km: number;
  duration_minutes: number;
  duration_text: string;
  route_geometry: [number, number][];
  osm_attribution: string;
  open_map_url: string;
  routing_service: string;
}

export async function calculateMedicalRoute(req: OpenRouteRequest): Promise<OpenRouteResponse> {
  return await fetchApi<OpenRouteResponse>('/travel/route', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export interface NearbyPOI {
  name: string;
  category: 'hotel' | 'pharmacy';
  address: string;
  lat: number;
  lon: number;
  distance_km?: number;
  open_map_url: string;
}

export interface NearbyPOIResponse {
  query_location: string;
  category: string;
  total_found: number;
  items: NearbyPOI[];
  osm_attribution: string;
}

export interface EmergencyContact {
  service_name: string;
  number: string;
  description: string;
}

export interface HospitalEmergencyDept {
  hospital_name: string;
  emergency_phone: string;
  address: string;
  city: string;
  state: string;
  emergency_24x7: boolean;
  icu_beds: number;
  lat?: number;
  lon?: number;
}

export interface EmergencyServicesResponse {
  city: string;
  state: string;
  national_emergency_number: string;
  ambulance_number: string;
  police_number: string;
  fire_number: string;
  women_helpline: string;
  contacts: EmergencyContact[];
  hospital_emergency_dept?: HospitalEmergencyDept;
  disclaimer: string;
}

export async function getNearbyPOIs(location: string, category: 'hotel' | 'pharmacy', limit = 5): Promise<NearbyPOIResponse> {
  const query = new URLSearchParams({
    location,
    category,
    limit: String(limit),
  });
  return await fetchApi<NearbyPOIResponse>(`/travel/nearby?${query.toString()}`);
}

export async function getEmergencyServices(city?: string, hospitalId?: number): Promise<EmergencyServicesResponse> {
  const query = new URLSearchParams();
  if (city) query.set('city', city);
  if (hospitalId) query.set('hospital_id', String(hospitalId));
  return await fetchApi<EmergencyServicesResponse>(`/travel/emergency?${query.toString()}`);
}


