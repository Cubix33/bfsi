import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, TrendingUp, FileText } from "lucide-react";
import Navbar from "@/components/Navbar";

const Results = () => {
  const navigate = useNavigate();

  const creditScore = 782;
  const maxScore = 900;
  const riskLevel = "Low";
  const preApprovedLimit = 500000;
  // This would normally come from backend, but for demo purposes it's hardcoded
  const decision = "approved" as "approved" | "needs_documents" | "rejected";

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Navbar />

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8 animate-fade-in">
            <h1 className="text-4xl font-bold text-foreground mb-3">Credit & Underwriting Results</h1>
            <p className="text-lg text-muted-foreground">
              We've assessed your creditworthiness
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            {/* Credit Score Card */}
            <Card className="border-2 shadow-xl animate-scale-in">
              <CardHeader className="bg-gradient-primary text-white">
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-6 w-6" />
                  Credit Score
                </CardTitle>
              </CardHeader>
              <CardContent className="p-8">
                <div className="text-center mb-6">
                  <div className="text-6xl font-bold text-primary mb-2">{creditScore}</div>
                  <p className="text-muted-foreground">out of {maxScore}</p>
                </div>
                <Progress value={(creditScore / maxScore) * 100} className="h-3 mb-4" />
                <div className="flex justify-center">
                  <Badge variant="outline" className="bg-success/10 text-success border-success text-lg px-4 py-2">
                    Excellent Score
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Risk Assessment Card */}
            <Card className="border-2 shadow-xl animate-scale-in" style={{ animationDelay: "100ms" }}>
              <CardHeader className="bg-gradient-primary text-white">
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-6 w-6" />
                  Risk Assessment
                </CardTitle>
              </CardHeader>
              <CardContent className="p-8">
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Risk Level</span>
                    <Badge
                      variant="outline"
                      className={
                        riskLevel === "Low"
                          ? "bg-success/10 text-success border-success"
                          : riskLevel === "Medium"
                          ? "bg-warning/10 text-warning border-warning"
                          : "bg-destructive/10 text-destructive border-destructive"
                      }
                    >
                      {riskLevel}
                    </Badge>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Pre-approved Limit</span>
                    <span className="text-2xl font-bold text-primary">
                      ₹{preApprovedLimit.toLocaleString("en-IN")}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Interest Rate</span>
                    <span className="text-xl font-semibold text-foreground">10.5% p.a.</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Decision Card */}
          <Card className="border-2 shadow-xl animate-fade-in-up">
            <CardHeader className={`text-white rounded-t-lg ${
              decision === "approved"
                ? "bg-success"
                : decision === "needs_documents"
                ? "bg-warning"
                : "bg-destructive"
            }`}>
              <CardTitle className="text-2xl flex items-center gap-3">
                {decision === "approved" ? (
                  <>
                    <CheckCircle className="h-8 w-8" />
                    Instant Approval!
                  </>
                ) : decision === "needs_documents" ? (
                  <>
                    <FileText className="h-8 w-8" />
                    Additional Documents Required
                  </>
                ) : (
                  <>Unable to Approve</>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-8">
              {decision === "approved" && (
                <>
                  <p className="text-lg text-muted-foreground mb-6 leading-relaxed">
                    Congratulations! Based on your excellent credit profile, your loan has been
                    pre-approved. You can now upload your salary slip to receive your final sanction
                    letter.
                  </p>
                  <div className="flex gap-4">
                    <Button
                      variant="outline"
                      size="lg"
                      className="flex-1"
                      onClick={() => navigate("/upload")}
                    >
                      <FileText className="mr-2 h-5 w-5" />
                      Upload Salary Slip
                    </Button>
                    <Button
                      variant="hero"
                      size="lg"
                      className="flex-1"
                      onClick={() => navigate("/approval")}
                    >
                      Generate Sanction Letter
                    </Button>
                  </div>
                </>
              )}

              {decision === "needs_documents" && (
                <>
                  <p className="text-lg text-muted-foreground mb-6 leading-relaxed">
                    Your application looks good! We need a few more documents to complete the
                    underwriting process. Please upload your salary slip to proceed.
                  </p>
                  <Button
                    variant="hero"
                    size="lg"
                    className="w-full"
                    onClick={() => navigate("/upload")}
                  >
                    <FileText className="mr-2 h-5 w-5" />
                    Upload Required Documents
                  </Button>
                </>
              )}

              {decision === "rejected" && (
                <>
                  <p className="text-lg text-muted-foreground mb-6 leading-relaxed">
                    Unfortunately, we're unable to approve your loan at this time based on your
                    current credit profile. You can reapply after 6 months or contact our support
                    team for assistance.
                  </p>
                  <div className="flex gap-4">
                    <Button variant="outline" size="lg" className="flex-1">
                      Contact Support
                    </Button>
                    <Button variant="default" size="lg" className="flex-1" onClick={() => navigate("/")}>
                      Return to Home
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Results;
