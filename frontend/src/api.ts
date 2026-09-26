export interface PatientInput {
  male: number;
  age: number;
  currentSmoker: number;
  cigsPerDay: number;
  BPMeds: number;
  prevalentStroke: number;
  prevalentHyp: number;
  diabetes: number;
  totChol: number;
  sysBP: number;
  diaBP: number;
  BMI: number;
  heartRate: number;
  glucose: number;
}

export interface PredictionResponse {
  risk_score: number;
  risk_percentage: number;
  risk_band: 'Low' | 'Borderline' | 'High';
  requires_recourse: boolean;
}

export interface FeatureAttribution {
  feature: string;
  display_name: string;
  attribution_value: number;
  patient_value: number;
  direction: 'risk_increasing' | 'protective';
  marginal_percentage_impact?: number;
}

export interface ExplanationResponse {
  base_value: number;
  risk_score: number;
  attributions: FeatureAttribution[];
  base_log_odds?: number;
  patient_log_odds?: number;
}


export interface FeatureDelta {
  feature: string;
  display_name: string;
  baseline_value: number;
  target_value: number;
  delta: number;
  unit: string;
}

export interface RecoursePathway {
  pathway_id: number;
  title: string;
  projected_risk_score: number;
  projected_risk_percentage: number;
  absolute_risk_reduction: number;
  changes: FeatureDelta[];
  full_target_vector: Record<string, number>;
}

export interface RecourseResponse {
  patient_baseline_risk: number;
  pathways: RecoursePathway[];
  is_fallback: boolean;
}

export interface AssessmentResponse {
  prediction: PredictionResponse;
  explanation: ExplanationResponse;
  recourse: RecourseResponse;
  total_latency_ms: number;
}

/**
 * Formats backend API error responses into clean, human-readable strings.
 * Parses Pydantic 422 validation error arrays, e.g.:
 * [{ loc: ["body", "sysBP"], msg: "Input should be greater than or equal to 70" }] -> "sysBP: Input should be greater than or equal to 70"
 * Ensures raw objects or unhandled structures are never stringified to "[object Object]".
 */
export function formatApiErrorMessage(errorData: any, defaultMessage: string): string {
  if (!errorData) return defaultMessage;

  // Handle Pydantic 422 array format: detail = [{ loc: [...], msg: "..." }]
  if (Array.isArray(errorData.detail)) {
    const formatted = errorData.detail.map((err: any) => {
      if (typeof err === 'string') return err;
      if (err && typeof err === 'object') {
        const field = Array.isArray(err.loc) && err.loc.length > 0
          ? String(err.loc[err.loc.length - 1])
          : null;
        const msg = err.msg || 'Invalid input';
        return field ? `${field}: ${msg}` : msg;
      }
      return String(err);
    });
    const result = formatted.filter(Boolean).join('; ');
    if (result && result !== '[object Object]') return result;
  }

  // Handle standard string detail: detail = "Patient not found"
  if (typeof errorData.detail === 'string' && errorData.detail.trim()) {
    return errorData.detail.trim();
  }

  // Handle detail as an object: detail = { message: "..." }
  if (errorData.detail && typeof errorData.detail === 'object') {
    if (typeof errorData.detail.message === 'string') {
      return errorData.detail.message;
    }
    if (typeof errorData.detail.msg === 'string') {
      return errorData.detail.msg;
    }
    try {
      return JSON.stringify(errorData.detail);
    } catch {
      return defaultMessage;
    }
  }

  // Handle errorData.message: message = "..."
  if (typeof errorData.message === 'string' && errorData.message.trim()) {
    return errorData.message.trim();
  }

  return defaultMessage;
}

export async function assessPatient(
  payload: PatientInput,
  externalSignal?: AbortSignal
): Promise<AssessmentResponse> {
  const controller = new AbortController();
  const timeoutMs = 10000;
  const timeoutId = setTimeout(() => {
    controller.abort(new Error('Inference request timed out after 10 seconds.'));
  }, timeoutMs);

  if (externalSignal) {
    externalSignal.addEventListener('abort', () => controller.abort());
  }

  try {
    const response = await fetch('/api/assess', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
      throw new Error(formatApiErrorMessage(errorData, `Server error: ${response.status}`));
    }

    return await response.json();
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error('Clinical inference SLA exceeded: The request timed out after 10 seconds.');
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ==========================================
// Doctor Portal & Authentication Contracts
// ==========================================

export interface DoctorUser {
  doctorId: string;
  email: string;
  fullName: string;
  specialization: string;
  hospital: string;
  createdAt?: string;
}

export interface DoctorAuthResponse {
  access_token: string;
  token_type: string;
  doctor: DoctorUser;
}

export interface DoctorOverview {
  totalPatients: number;
  highRiskCount: number;
  borderlineCount: number;
  lowRiskCount: number;
  notAssessedCount?: number;
}

export interface PatientRecord {
  patientId: string;
  doctorId: string;
  fullName: string;
  age: number;
  sex: string;
  contactPhone: string;
  baselineBiomarkers: Partial<PatientInput>;
  latestRiskScore: number | null;
  latestRiskPercentage: number | null;
  latestRiskBand: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreatePatientPayload {
  fullName: string;
  age: number;
  sex: string;
  contactPhone?: string;
  baselineBiomarkers?: Partial<PatientInput>;
}

export interface UpdatePatientPayload {
  fullName?: string;
  age?: number;
  sex?: string;
  contactPhone?: string;
  baselineBiomarkers?: Partial<PatientInput>;
}

export interface PatientAssessmentRecord {
  assessmentId: string;
  patientId: string;
  assessedAt: string;
  riskScore: number;
  riskPercentage: number;
  riskBand: string;
  inputBiomarkers: Record<string, number>;
  shapAttributions: FeatureAttribution[];
  pipelineLatencyMs: number;
}

export interface PatientActionPlanRecord {
  planId: string;
  patientId: string;
  assessmentId: string;
  createdAt: string;
  selectedPathwayTitle: string;
  projectedRiskPercentage: number;
  absoluteRiskReduction: number;
  targetBiomarkers: Record<string, number>;
  recommendedChanges: FeatureDelta[];
  clinicianNotes: string;
  doctorConfirmed: boolean;
}

export interface PatientHistory {
  patientId: string;
  assessments: PatientAssessmentRecord[];
  actionPlans: PatientActionPlanRecord[];
}

export interface DoctorAssessmentResponse extends AssessmentResponse {
  assessment_id: string;
  patient_id: string;
}

// ------------------------------------------
// Doctor Authentication API Calls
// ------------------------------------------

export async function loginDoctor(email: string, password: string): Promise<DoctorAuthResponse> {
  const response = await fetch('/api/auth/doctor/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Authentication failed' }));
    throw new Error(formatApiErrorMessage(errorData, `Login error: ${response.status}`));
  }
  return response.json();
}

export async function registerDoctor(payload: {
  email: string;
  password: string;
  fullName: string;
  specialization?: string;
  hospital?: string;
  createdAt?: string;
}): Promise<DoctorAuthResponse> {
  const response = await fetch('/api/auth/doctor/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(formatApiErrorMessage(errorData, `Registration error: ${response.status}`));
  }
  return response.json();
}

export async function logoutDoctor(token: string): Promise<void> {
  try {
    await fetch('/api/auth/doctor/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    // Graceful no-op on logout network errors
  }
}

export async function getDoctorOverview(token: string): Promise<DoctorOverview> {
  const response = await fetch('/api/doctor/overview', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to retrieve clinical overview' }));
    throw new Error(formatApiErrorMessage(errorData, 'Failed to retrieve clinical overview'));
  }
  return response.json();
}

export async function listPatients(
  token: string,
  search?: string,
  riskBand?: string
): Promise<PatientRecord[]> {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (riskBand && riskBand !== 'All') params.append('risk_band', riskBand);

  const url = `/api/doctor/patients${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to retrieve patient registry' }));
    throw new Error(formatApiErrorMessage(errorData, 'Failed to retrieve patient registry'));
  }
  return response.json();
}

export async function createPatient(
  token: string,
  payload: CreatePatientPayload
): Promise<PatientRecord> {
  const response = await fetch('/api/doctor/patients', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create patient' }));
    throw new Error(formatApiErrorMessage(errorData, 'Failed to create patient'));
  }
  return response.json();
}

export async function updatePatient(
  token: string,
  patientId: string,
  payload: UpdatePatientPayload
): Promise<PatientRecord> {
  const response = await fetch(`/api/doctor/patients/${patientId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to update patient record' }));
    throw new Error(formatApiErrorMessage(errorData, 'Failed to update patient record'));
  }
  return response.json();
}

export async function getPatientHistory(token: string, patientId: string): Promise<PatientHistory> {
  const response = await fetch(`/api/doctor/patients/${patientId}/history`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to retrieve patient clinical timeline' }));
    throw new Error(formatApiErrorMessage(errorData, 'Failed to retrieve patient clinical timeline'));
  }
  return response.json();
}

export async function assessDoctorPatient(
  token: string,
  patientId: string,
  biomarkers?: Partial<PatientInput>
): Promise<DoctorAssessmentResponse> {
  const response = await fetch(`/api/doctor/patients/${patientId}/assess`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ biomarkers: biomarkers || null }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Clinical assessment failed' }));
    throw new Error(formatApiErrorMessage(errorData, 'Clinical assessment failed'));
  }
  return response.json();
}

export async function saveDoctorActionPlan(
  token: string,
  patientId: string,
  payload: {
    assessmentId: string;
    selectedPathwayTitle: string;
    projectedRiskPercentage: number;
    absoluteRiskReduction: number;
    targetBiomarkers: Record<string, number>;
    recommendedChanges: FeatureDelta[];
    clinicianNotes?: string;
    doctorConfirmed?: boolean;
  }
): Promise<{ status: string; message: string; plan: PatientActionPlanRecord }> {
  const response = await fetch(`/api/doctor/patients/${patientId}/action-plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to save action plan' }));
    throw new Error(formatApiErrorMessage(errorData, 'Failed to save action plan'));
  }
  return response.json();
}

