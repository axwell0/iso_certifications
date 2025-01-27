import { Button } from "../components/ui/button";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary">
      <div className="container mx-auto px-4 py-16 animate-fadeIn">
        <nav className="flex justify-between items-center mb-16">
          <div className="text-2xl font-bold text-primary">CertiPro</div>
          <Button
            variant="outline"
            className="hover:bg-primary hover:text-white transition-colors"
            onClick={() => navigate("/login")}
          >
            Sign In
          </Button>
        </nav>

        <main className="max-w-4xl mx-auto text-center space-y-8">
          <div className="space-y-4 animate-slideUp">
            <h1 className="text-5xl font-bold text-primary tracking-tight">
              Certification Management,{" "}
              <span className="text-accent">Simplified</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Streamline your ISO certification process with our comprehensive
              platform designed for certification bodies and organizations.
            </p>
          </div>

          <div className="flex justify-center gap-4 pt-8 animate-slideUp" style={{ animationDelay: "0.2s" }}>
            <Button
              size="lg"
              className="bg-primary text-white hover:bg-primary/90 transition-colors"
              onClick={() => navigate("/register")}
            >
              Get Started
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="hover:bg-secondary transition-colors"
              onClick={() => navigate("/about")}
            >
              Learn More
            </Button>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-left animate-slideUp" style={{ animationDelay: "0.4s" }}>
            <div className="bg-card p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-lg font-semibold mb-2 text-primary">
                ISO Standards Management
              </h3>
              <p className="text-muted-foreground">
                Comprehensive tools for managing ISO standards and certifications.
              </p>
            </div>
            <div className="bg-card p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-lg font-semibold mb-2 text-primary">
                Audit Tracking
              </h3>
              <p className="text-muted-foreground">
                Efficiently schedule, conduct, and track audits in one place.
              </p>
            </div>
            <div className="bg-card p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-lg font-semibold mb-2 text-primary">
                Certification Issuance
              </h3>
              <p className="text-muted-foreground">
                Streamlined process for issuing and managing certifications.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Index;