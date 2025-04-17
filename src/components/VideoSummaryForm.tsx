import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingIndicator } from "@/components/LoadingIndicator";
import { FileVideo } from "lucide-react";

interface VideoSummaryFormProps {
  onSubmit?: (url: string) => void; // Optional if handling API directly
  isLoading?: boolean;
}

interface JobStatus {
  status: 'queued' | 'downloading' | 'transcribing' | 'summarizing' | 'completed' | 'failed';
  summary?: string;
  error?: string;
  progress?: string;
}

export const VideoSummaryForm = ({ onSubmit, isLoading: externalLoading }: VideoSummaryFormProps) => {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [processingStage, setProcessingStage] = useState("");

  // Use external loading state if provided, otherwise use internal state
  const loading = externalLoading !== undefined ? externalLoading : isLoading;

  // Poll for job status updates if handling API directly
  useEffect(() => {
    if (!jobId) return;
    
    const checkStatus = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/status/${jobId}`);
        const data = await response.json();
        
        setJobStatus(data);
        
        // Update processing stage for UI feedback
        if (data.status === 'downloading') {
          setProcessingStage("Downloading video...");
        } else if (data.status === 'transcribing') {
          setProcessingStage("Transcribing audio...");
        } else if (data.status === 'summarizing') {
          setProcessingStage(data.progress || "Generating summary...");
        }
        
        if (data.status === 'completed') {
          setSummary(data.summary);
          setIsLoading(false);
          // If parent component provided onSummaryReady callback, call it
          if (onSummaryReady) onSummaryReady(data.summary);
        } else if (data.status === 'failed') {
          setError(data.error || 'Failed to generate summary');
          setIsLoading(false);
          setJobId(null);
        } else {
          // Continue polling for non-completed statuses
          setTimeout(checkStatus, 2000);
        }
      } catch (err) {
        setError('Error checking job status');
        setIsLoading(false);
        setJobId(null);
      }
    };
    
    checkStatus();
  }, [jobId]);

  const validateUrl = (input: string) => {
    if (!input.trim()) {
      return "Please enter a URL";
    }
    
    // Accept both direct MP4 URLs and YouTube URLs
    const isMP4 = input.toLowerCase().includes('.mp4');
    const isYouTube = input.includes('youtube.com') || input.includes('youtu.be');
    
    if (!isMP4 && !isYouTube) {
      return "Please enter a valid MP4 or YouTube URL";
    }
    
    return "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateUrl(url);
    
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setError("");
    
    // If parent component provided onSubmit callback, use it
    if (onSubmit) {
      onSubmit(url);
      return;
    }
    
    // Otherwise handle API call directly
    setIsLoading(true);
    setSummary("");
    setJobId(null);
    setProcessingStage("Starting process...");
    
    try {
      const response = await fetch('http://localhost:5000/api/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ videoUrl: url }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to start summarization');
      }
      
      setJobId(data.jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      setIsLoading(false);
    }
  };

  // Optional callback for when summary is ready
  const onSummaryReady = (text: string) => {
    // This can be implemented if needed to notify parent component
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="video-url" className="text-lg font-medium">
            Video URL
          </Label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                <FileVideo size={18} />
              </div>
              <Input
                id="video-url"
                placeholder="Enter MP4 video or YouTube URL"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="pl-10"
                disabled={loading}
              />
            </div>
            <Button 
              type="submit" 
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {loading ? (
                <LoadingIndicator size="sm" />
              ) : (
                "Generate Summary"
              )}
            </Button>
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
        <p className="text-sm text-gray-500">
          Paste the direct link to any MP4 video file or YouTube URL to generate a text summary using our NLP model.
        </p>
      </form>
      
      {/* Display processing status if handling API directly */}
      {isLoading && !externalLoading && (
        <div className="mt-4 p-4 border rounded-lg bg-gray-50">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8">
              <div className="animate-spin h-full w-full border-4 border-gray-300 border-t-indigo-600 rounded-full"></div>
            </div>
            <div>
              <h3 className="font-medium">Processing Your Video</h3>
              <p className="text-sm text-gray-500">{processingStage}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Display summary if handling API directly */}
      {summary && !onSubmit && (
        <div className="mt-6 p-6 border rounded-lg bg-white">
          <h3 className="text-xl font-medium mb-4">Summary</h3>
          <p className="text-gray-700 whitespace-pre-line">{summary}</p>
          <div className="mt-4 flex justify-end">
            <Button 
              onClick={() => navigator.clipboard.writeText(summary)}
              variant="outline"
              className="text-indigo-600"
            >
              Copy to Clipboard
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};