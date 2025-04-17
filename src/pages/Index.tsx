
import { useState } from "react";
import { api } from "@/lib/api";
import { VideoSummaryForm } from "@/components/VideoSummaryForm";
import { SummaryResult } from "@/components/SummaryResult";
import { Hero } from "@/components/Hero";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";



const Index = () => {
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const handleGenerateSummary = async (url: string) => {
    console.log("▶️ handleGenerateSummary fired for URL:", url);
    setIsLoading(true);
    setVideoUrl(url);
    
    try {
      const { jobId } = await api.startSummarization(url);
  
      let statusResponse = await api.checkStatus(jobId);
      while (statusResponse.status !== "completed" && statusResponse.status !== "failed") {
        await new Promise(resolve => setTimeout(resolve, 3000));
        statusResponse = await api.checkStatus(jobId);
      }
  
      if (statusResponse.status === "completed" && statusResponse.summary) {
        setSummary(statusResponse.summary);
        toast.success("Summary generated successfully!");
      } else {
        toast.error("Summary generation failed.");
      }
    } catch (error) {
      console.error("Error generating summary:", error);
      toast.error("Failed to generate summary. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };
  

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-10 max-w-5xl">
        <Hero />
        
        <Card className="p-6 shadow-lg mt-8">
          <VideoSummaryForm onSubmit={handleGenerateSummary} isLoading={isLoading} />
        </Card>
        
        {(summary || isLoading) && (
          <Card className="p-6 shadow-lg mt-8">
            <SummaryResult 
              summary={summary} 
              isLoading={isLoading} 
              videoUrl={videoUrl} 
            />
          </Card>
        )}
      </div>
    </div>
  );
};

export default Index;
