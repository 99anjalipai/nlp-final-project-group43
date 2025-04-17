
import { LoadingIndicator } from "@/components/LoadingIndicator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SummaryResultProps {
  summary: string | null;
  isLoading: boolean;
  videoUrl: string | null;
}

export const SummaryResult = ({ summary, isLoading, videoUrl }: SummaryResultProps) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Summary Result</h3>
        {videoUrl && (
          <span className="text-sm text-gray-500 truncate max-w-md">
            {videoUrl}
          </span>
        )}
      </div>
      
      <div className="bg-gray-50 rounded-lg p-4 min-h-32">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-32 space-y-2">
            <LoadingIndicator size="lg" />
            <p className="text-gray-500 animate-pulse">Analyzing video content...</p>
          </div>
        ) : summary ? (
          <ScrollArea className="h-60">
            <div className="text-gray-700 whitespace-pre-line">
              {summary}
            </div>
          </ScrollArea>
        ) : null}
      </div>
      
      {summary && !isLoading && (
        <div className="flex justify-end gap-2">
          <button
            onClick={() => navigator.clipboard.writeText(summary)}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            Copy to clipboard
          </button>
          {/* Additional actions can be added here */}
        </div>
      )}
    </div>
  );
};
