import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Download, ArrowLeft, Building2 } from "lucide-react";
import Navbar from "@/components/Navbar";

const SanctionLetter = () => {
  const navigate = useNavigate();
  const { id } = useParams();

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Navbar />

      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <Button variant="hero">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
        </div>

        <Card className="border-2 shadow-xl max-w-4xl mx-auto">
          <CardContent className="p-12">
            {/* PDF-like Letter Content */}
            <div className="space-y-8">
              {/* Header */}
              <div className="text-center border-b pb-6">
                <div className="flex items-center justify-center gap-3 mb-4">
                  <Building2 className="h-12 w-12 text-primary" />
                  <div>
                    <h1 className="text-3xl font-bold text-primary">Tata Capital Limited</h1>
                    <p className="text-sm text-muted-foreground">Personal Loan Division</p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Corporate Office: Mumbai, Maharashtra | CIN: U65910MH1991PLC123456
                </p>
              </div>

              {/* Letter Title */}
              <div className="text-center">
                <h2 className="text-2xl font-bold text-foreground mb-2">LOAN SANCTION LETTER</h2>
                <p className="text-muted-foreground">Sanction ID: {id || "TCSL2025001234"}</p>
                <p className="text-muted-foreground">Date: {new Date().toLocaleDateString()}</p>
              </div>

              {/* To Section */}
              <div>
                <p className="font-semibold mb-2">To,</p>
                <p className="text-foreground">Mr. John Doe</p>
                <p className="text-muted-foreground">123 Main Street</p>
                <p className="text-muted-foreground">Mumbai, Maharashtra - 400001</p>
              </div>

              {/* Subject */}
              <div>
                <p className="font-semibold">Subject: Sanction of Personal Loan</p>
              </div>

              {/* Body */}
              <div className="space-y-4 text-justify leading-relaxed">
                <p>Dear Mr. John Doe,</p>
                <p>
                  We are pleased to inform you that your application for a Personal Loan has been
                  approved by Tata Capital Limited. This sanction is based on the information and
                  documents provided by you and is subject to the terms and conditions mentioned below.
                </p>
              </div>

              {/* Loan Details Table */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-primary/5">
                    <tr>
                      <th className="text-left p-4 font-semibold border-b">Particulars</th>
                      <th className="text-right p-4 font-semibold border-b">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="p-4 text-muted-foreground">Loan Amount Sanctioned</td>
                      <td className="p-4 text-right font-semibold">₹5,00,000</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-4 text-muted-foreground">Rate of Interest</td>
                      <td className="p-4 text-right font-semibold">10.5% p.a.</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-4 text-muted-foreground">Loan Tenure</td>
                      <td className="p-4 text-right font-semibold">36 months</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-4 text-muted-foreground">EMI Amount</td>
                      <td className="p-4 text-right font-semibold">₹16,134</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-4 text-muted-foreground">Processing Fee</td>
                      <td className="p-4 text-right font-semibold">₹10,000 + GST</td>
                    </tr>
                    <tr>
                      <td className="p-4 text-muted-foreground">Repayment Mode</td>
                      <td className="p-4 text-right font-semibold">Monthly EMI via Auto-debit</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Terms & Conditions */}
              <div className="space-y-3">
                <p className="font-semibold">Terms & Conditions:</p>
                <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                  <li>This sanction is valid for 30 days from the date of this letter.</li>
                  <li>
                    The loan will be disbursed subject to verification of all submitted documents.
                  </li>
                  <li>
                    The borrower must maintain a minimum credit score of 700 throughout the loan tenure.
                  </li>
                  <li>Pre-payment charges may apply as per the loan agreement.</li>
                  <li>
                    Any default in EMI payment will attract penalty charges and affect your credit score.
                  </li>
                </ol>
              </div>

              {/* Closing */}
              <div className="space-y-4">
                <p>
                  Please contact our customer care at <strong>1800-XXX-XXXX</strong> for any queries
                  or clarifications.
                </p>
                <p>We look forward to serving you.</p>
                <div className="mt-8">
                  <p className="font-semibold">Yours sincerely,</p>
                  <p className="mt-2 font-semibold text-primary">Tata Capital Limited</p>
                  <p className="text-sm text-muted-foreground">Authorized Signatory</p>
                </div>
              </div>

              {/* Footer */}
              <div className="border-t pt-6 text-center text-xs text-muted-foreground">
                <p>This is a computer-generated letter and does not require a physical signature.</p>
                <p className="mt-2">
                  For more information, visit www.tatacapital.com | Email: support@tatacapital.com
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SanctionLetter;
