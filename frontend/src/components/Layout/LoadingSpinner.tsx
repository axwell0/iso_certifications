// src/components/Layout/LoadingSpinner.tsx
import { Loader2 } from "lucide-react";

export const LoadingSpinner = () => (
  <div className="fixed inset-0 bg-background/50 backdrop-blur-sm z-50 flex items-center justify-center">
    <Loader2 className="h-12 w-12 animate-spin text-primary" />
  </div>
);