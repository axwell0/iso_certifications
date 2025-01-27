// src/pages/Unauthorized.tsx
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const Unauthorized = () => (
  <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground p-4">
    <div className="max-w-md text-center space-y-4">
      <h1 className="text-4xl font-bold">401 - Unauthorized</h1>
      <p className="text-muted-foreground">
        You don't have permission to access this page
      </p>
      <Button asChild variant="outline">
        <Link to="/login" className="mt-4">
          Return to Login
        </Link>
      </Button>
    </div>
  </div>
);

export default Unauthorized;