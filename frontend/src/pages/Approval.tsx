import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle, Download, Home } from "lucide-react";
import Navbar from "@/components/Navbar";
import { useEffect, useState } from "react";

const Approval = () => {
  const navigate = useNavigate();
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 5000);
  }, []);

  const loanDetails = {
    customerName: "John Doe",
    loanAmount: 500000,
    tenure: 36,
    interestRate: 10.5,
    emi: 16134,
    sanctionId: "TCSL2025001234",
  };

  const handleDownload = () => {
    // In real app, this would trigger PDF download
    window.open("/sanction-letter/TCSL2025001234", "_blank");
  };

  return (
    <div className="min-h-screen bg-gradient-subtle relative overflow-hidden">
      <Navbar />

      {/* Confetti Effect */}
      {showConfetti && (
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-primary rounded-full animate-bounce"
              style={{
                left: `${Math.random() * 100}%`,
                top: `-${Math.random() * 20}%`,
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${2 + Math.random() * 3}s`,
              }}
            />
          ))}
        </div>
      )}

      <div className="container mx-auto px-4 py-12 relative z-10">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-8 animate-scale-in">
            <div className="mx-auto w-24 h-24 rounded-full bg-success/10 flex items-center justify-center mb-6">
              <CheckCircle className="h-16 w-16 text-success fill-success" />
            </div>
            <h1 className="text-5xl font-bold text-success mb-4">Congratulations!</h1>
            <p className="text-2xl text-foreground mb-2">Your Loan is Approved</p>
            <p className="text-lg text-muted-foreground">
              You can now download your sanction letter
            </p>
          </div>

          <Card className="border-2 shadow-2xl animate-fade-in-up">
            <CardContent className="p-8">
              <div className="bg-gradient-primary text-white p-6 rounded-lg mb-6">
                <h2 className="text-2xl font-bold mb-4">Sanction Letter Details</h2>
                <div className="space-y-2">
                  <p className="text-white/90">Sanction ID: {loanDetails.sanctionId}</p>
                  <p className="text-white/90">Date: {new Date().toLocaleDateString()}</p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Borrower Name</p>
                    <p className="text-lg font-semibold text-foreground">{loanDetails.customerName}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Loan Amount</p>
                    <p className="text-2xl font-bold text-primary">
                      ₹{loanDetails.loanAmount.toLocaleString("en-IN")}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Tenure</p>
                    <p className="text-lg font-semibold text-foreground">{loanDetails.tenure} months</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Interest Rate</p>
                    <p className="text-lg font-semibold text-foreground">{loanDetails.interestRate}% p.a.</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Monthly EMI</p>
                    <p className="text-2xl font-bold text-primary">
                      ₹{loanDetails.emi.toLocaleString("en-IN")}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Status</p>
                    <div className="inline-flex items-center gap-2 bg-success/10 text-success px-3 py-1 rounded-full">
                      <CheckCircle className="h-4 w-4" />
                      <span className="font-semibold">Approved</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t pt-6 space-y-4">
                <Button variant="hero" size="lg" className="w-full" onClick={handleDownload}>
                  <Download className="mr-2 h-5 w-5" />
                  Download Sanction Letter
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full"
                  onClick={() => navigate("/dashboard")}
                >
                  <Home className="mr-2 h-5 w-5" />
                  Go to Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="mt-8 text-center animate-fade-in" style={{ animationDelay: "300ms" }}>
            <p className="text-muted-foreground mb-2">
              Need help? Contact our support team
            </p>
            <p className="text-primary font-semibold">1800-XXX-XXXX</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Approval;
