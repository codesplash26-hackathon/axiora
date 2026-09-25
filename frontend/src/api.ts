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
}

export interface ExplanationResponse {
  base_value: number;
  risk_score: number;
  attributions: FeatureAttribution[];
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
      throw new Error(errorData.detail || `Server error: ${response.status}`);
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
