import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { CheckCircle2 } from "lucide-react";

const EmailConfirmation = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const token = searchParams.get("token");

  useEffect(() => {
    const verifyEmail = async () => {
      try {
        if (!token) {
          throw new Error("No token provided");
        }

        const response = await fetch(`https://127.0.0.1:5000/auth/verify-email?token=${token}`, {
          method: "GET",
        });

        const data = await response.json();

        if (!response.ok || data.message !== "Email confirmed successfully.") {
          throw new Error(data.error || "Email verification failed");
        }
        localStorage.clear();
        localStorage.setItem("accessToken", data.access_token);

        setIsOpen(true);
        toast({
          title: "Email verified successfully",
          description: "Redirecting...",
        });

        setTimeout(() => {
          setIsOpen(false);
          navigate("/dashboard");
        }, 2000);
      } catch (error) {
        console.error("Verification error:", error);
        toast({
          title: "Verification failed",
          description: "Please try again or contact support",
          variant: "destructive",
        });
        navigate("/login");
      }
    };

    if (token) {
      verifyEmail();
    } else {
      navigate("/login");
    }
  }, [token, navigate, toast]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-center">Email Verified!</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col items-center justify-center space-y-4 py-6">
            <CheckCircle2 className="h-16 w-16 text-primary animate-scale-in" />
            <p className="text-center text-muted-foreground">
              Your email has been successfully verified. Redirecting you to the dashboard...
            </p>
          </div>
        </DialogContent>
      </Dialog>
      <div className="text-center animate-pulse">
        <p className="text-lg text-muted-foreground">Verifying your email...</p>
      </div>
    </div>
  );
};

export default EmailConfirmation;