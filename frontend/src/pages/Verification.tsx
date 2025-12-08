import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { Shield } from "lucide-react";
import Navbar from "@/components/Navbar";
import { toast } from "sonner";

const Verification = () => {
  const navigate = useNavigate();
  const [phone, setPhone] = useState("+91 9876543210");
  const [otp, setOtp] = useState("");
  const [address, setAddress] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);

  const handleVerify = () => {
    if (!otp || otp.length < 6) {
      toast.error("Please enter a valid 6-digit OTP");
      return;
    }

    if (!address.trim()) {
      toast.error("Please enter your address");
      return;
    }

    setIsVerifying(true);
    setTimeout(() => {
      toast.success("Verification successful!");
      navigate("/results");
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Navbar />

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8 animate-fade-in">
            <div className="mx-auto w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Shield className="h-10 w-10 text-primary" />
            </div>
            <h1 className="text-4xl font-bold text-foreground mb-3">Identity Verification</h1>
            <p className="text-lg text-muted-foreground">
              We need to verify your identity for security purposes
            </p>
          </div>

          <Card className="border-2 shadow-xl animate-scale-in">
            <CardHeader className="bg-gradient-primary text-white rounded-t-lg">
              <CardTitle className="text-2xl">KYC Verification</CardTitle>
            </CardHeader>
            <CardContent className="p-8 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled
                  className="bg-muted"
                />
                <p className="text-sm text-muted-foreground">
                  An OTP has been sent to this number
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="otp">Enter OTP</Label>
                <div className="flex justify-center py-4">
                  <InputOTP maxLength={6} value={otp} onChange={setOtp}>
                    <InputOTPGroup>
                      <InputOTPSlot index={0} />
                      <InputOTPSlot index={1} />
                      <InputOTPSlot index={2} />
                      <InputOTPSlot index={3} />
                      <InputOTPSlot index={4} />
                      <InputOTPSlot index={5} />
                    </InputOTPGroup>
                  </InputOTP>
                </div>
                <div className="text-center">
                  <Button variant="link" size="sm">
                    Resend OTP
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="address">Residential Address</Label>
                <Input
                  id="address"
                  type="text"
                  placeholder="Enter your complete address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="h-20"
                />
              </div>

              <Button
                variant="hero"
                size="lg"
                className="w-full"
                onClick={handleVerify}
                disabled={isVerifying}
              >
                {isVerifying ? "Verifying..." : "Verify Now"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Verification;
