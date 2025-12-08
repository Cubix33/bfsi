import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { IndianRupee, Calendar, Percent, CreditCard } from "lucide-react";
import Navbar from "@/components/Navbar";

const Summary = () => {
  const navigate = useNavigate();

  const loanDetails = {
    amount: 500000,
    tenure: 36,
    interestRate: 10.5,
    emi: 16134,
    totalInterest: 80824,
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Navbar />

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-8 animate-fade-in">
            <h1 className="text-4xl font-bold text-foreground mb-3">Loan Summary</h1>
            <p className="text-lg text-muted-foreground">
              Review your loan details before proceeding
            </p>
          </div>

          <Card className="border-2 shadow-xl animate-scale-in">
            <CardHeader className="bg-gradient-primary text-white rounded-t-lg">
              <CardTitle className="text-2xl">Your Loan Details</CardTitle>
            </CardHeader>
            <CardContent className="p-8 space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="flex items-start gap-4 p-4 bg-accent/50 rounded-lg">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <IndianRupee className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Loan Amount</p>
                    <p className="text-2xl font-bold text-foreground">
                      ₹{loanDetails.amount.toLocaleString("en-IN")}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4 p-4 bg-accent/50 rounded-lg">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <Calendar className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Tenure</p>
                    <p className="text-2xl font-bold text-foreground">{loanDetails.tenure} months</p>
                  </div>
                </div>

                <div className="flex items-start gap-4 p-4 bg-accent/50 rounded-lg">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <Percent className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Interest Rate</p>
                    <p className="text-2xl font-bold text-foreground">{loanDetails.interestRate}% p.a.</p>
                  </div>
                </div>

                <div className="flex items-start gap-4 p-4 bg-accent/50 rounded-lg">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <CreditCard className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Monthly EMI</p>
                    <p className="text-2xl font-bold text-primary">
                      ₹{loanDetails.emi.toLocaleString("en-IN")}
                    </p>
                  </div>
                </div>
              </div>

              <div className="border-t pt-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-muted-foreground">Total Interest Payable</span>
                  <span className="text-xl font-semibold text-foreground">
                    ₹{loanDetails.totalInterest.toLocaleString("en-IN")}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-foreground">Total Amount Payable</span>
                  <span className="text-2xl font-bold text-primary">
                    ₹{(loanDetails.amount + loanDetails.totalInterest).toLocaleString("en-IN")}
                  </span>
                </div>
              </div>

              <div className="flex gap-4 pt-6">
                <Button
                  variant="outline"
                  size="lg"
                  className="flex-1"
                  onClick={() => navigate("/chat")}
                >
                  Edit Details
                </Button>
                <Button
                  variant="hero"
                  size="lg"
                  className="flex-1"
                  onClick={() => navigate("/verify")}
                >
                  Confirm & Proceed
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Summary;
