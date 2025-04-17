
import { cn } from "@/lib/utils";

interface LoadingIndicatorProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const LoadingIndicator = ({ size = "md", className }: LoadingIndicatorProps) => {
  const sizeClasses = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-3",
    lg: "h-12 w-12 border-4",
  };

  return (
    <div
      className={cn(
        "animate-spin rounded-full border-t-transparent border-indigo-600",
        sizeClasses[size],
        className
      )}
      aria-label="Loading"
    />
  );
};
