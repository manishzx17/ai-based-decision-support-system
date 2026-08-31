// API Client for 12C Medical Travel Decision Support System

const BASE_URL = '/api';

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: 'API Error' }));
      throw new Error(errData.detail || `HTTP Error ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`API call ${endpoint} failed, utilizing local fallback data`, err);
    throw err;
  }
}

// Upload Report Helper (Multipart)
export async function uploadReportApi(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE_URL}/reports/upload?user_id=1`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error('Report upload failed');
  }
  return await res.json();
}
