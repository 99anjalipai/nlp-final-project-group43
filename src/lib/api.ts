const API_BASE_URL = 'http://localhost:5000/api';

export interface JobStatus {
  status: 'queued' | 'downloading' | 'transcribing' | 'summarizing' | 'completed' | 'failed';
  videoUrl: string;
  summary?: string;
  error?: string;
  progress?: string;
}

export const api = {
  async startSummarization(videoUrl: string): Promise<{ jobId: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/summarize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ videoUrl }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to start summarization');
    }
    
    return response.json();
  },

  async checkStatus(jobId: string): Promise<JobStatus> {
    const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
    
    if (!response.ok) {
      throw new Error('Failed to check status');
    }
    
    return response.json();
  },

  async evaluateSummary(reference: string, generated: string) {
    const response = await fetch(`${API_BASE_URL}/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ reference, generated }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to evaluate summary');
    }
    
    return response.json();
  },
};
