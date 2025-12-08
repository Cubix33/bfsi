import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Send, Upload, Bot, User } from "lucide-react";
import Navbar from "@/components/Navbar";

type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

const Chat = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello 👋 I’m your AI Loan Assistant from Tata Capital.\n\nTo get started, could you please share your registered phone number?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentStage, setCurrentStage] = useState(1);

  const stages = [
    "Initial",
    "Needs Assessment",
    "Verification",
    "Credit Check",
    "Underwriting",
    "Document Upload",
    "Approval",
  ];

  const simulateResponse = (text: string) => {
    const lowerInput = text.toLowerCase();
    let response = "";

    if (messages.length === 1) {
      response =
        "Thank you! Let me fetch your profile... ✅\n\nFound you — Riya Sharma, Age 28, from Delhi.\n\nYour current credit score is 782, and you have a pre-approved limit of ₹5,00,000.\n\nWould you like to explore a loan offer today?";
    } else if (lowerInput.includes("yes") && messages.length === 3) {
      response =
        "Perfect! 🎯\n\nCould you please tell me how much you’d like to borrow and for how long (in months or years)?";
      setCurrentStage(2);
    } else if (lowerInput.includes("4,00,000") || lowerInput.includes("400000")) {
      response =
        "Got it ✅\n\n💰 Loan Amount: ₹4,00,000\n📆 Tenure: 24 months\n🏦 Interest Rate: 11.5%\n💸 Monthly EMI: ₹18,744\n💰 Total Payable: ₹4,49,856\n\nWould you like to proceed with this offer?";
    } else if (lowerInput.includes("proceed")) {
      response =
        "Great! 🔐\n\nBefore we continue, please confirm your address and enter the OTP sent to your registered number.";
      setCurrentStage(3);
    } else if (lowerInput.includes("rohini") || lowerInput.includes("otp")) {
      response =
        "✅ Verification successful!\n\nNow performing a quick credit check based on your latest score...";
      setCurrentStage(4);
    } else if (lowerInput.includes("check")) {
      response =
        "Your credit score is 782 — excellent 🎉\n\nYou’re eligible for instant approval up to ₹5,00,000.\n\nLet’s move to underwriting to confirm the final decision.";
      setCurrentStage(5);
    } else if (lowerInput.includes("analyze")) {
      response =
        "Analyzing your profile... 🤖\n\n✅ Ratio of requested amount to pre-approved limit = 0.8\n✅ Risk Score: Low\n✅ Credit Score: Excellent\n\n🎉 You’re eligible for instant approval!\n\nPlease upload your latest salary slip (PDF) for compliance.";
      setCurrentStage(6);
    } else if (lowerInput.includes("upload")) {
      response =
        "✅ Received SalarySlip_Riya_Sharma.pdf\n\nExtracting income details...\n\n💼 Monthly Income: ₹60,000\n📊 EMI-to-Income Ratio: 31.2%\n\n✅ Looks great! You’re within the safe range.";
    } else if (messages.length >= 15) {
      response =
        "🎉 Congratulations, Riya!\n\nYour loan for ₹4,00,000 has been approved.\n\nI'm generating your sanction letter now... 📝\n\n✅ Sanction Letter: SanctionLetter_Riya_Sharma_20251104.pdf\n\nYou can view or download it from your dashboard anytime.";
      setCurrentStage(7);
    } else {
      response = "I understand. Could you please rephrase or provide more details?";
    }

    return response;
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      const response = simulateResponse(input);
      const aiMessage: Message = {
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const userMessage: Message = {
      role: "user",
      content: `📂 Uploaded file: ${file.name}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsTyping(true);
    setTimeout(() => {
      const aiMessage: Message = {
        role: "assistant",
        content:
          "✅ Received SalarySlip_Riya_Sharma.pdf\n\nExtracting income details...\n\n💼 Monthly Income: ₹60,000\n📊 EMI-to-Income Ratio: 31.2%\n\n✅ Looks great! You’re within the safe range.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
      setCurrentStage(7);
    }, 2000);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Navbar />

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar - Stages */}
          <div className="lg:col-span-1">
            <Card className="p-6 sticky top-24 text-base">
              <h3 className="font-semibold text-xl mb-5 text-foreground">
                Application Stages
              </h3>
              <div className="space-y-3">
                {stages.map((stage, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 transition-all ${
                      idx + 1 === currentStage
                        ? "text-primary font-semibold"
                        : idx + 1 < currentStage
                        ? "text-success"
                        : "text-muted-foreground"
                    }`}
                  >
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center text-sm ${
                        idx + 1 === currentStage
                          ? "bg-primary text-white"
                          : idx + 1 < currentStage
                          ? "bg-success text-white"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {idx + 1}
                    </div>
                    <span className="text-[0.95rem]">{stage}</span>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-6 border-t">
                <div className="space-y-3 text-base">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Credit Score</span>
                    <Badge
                      variant="outline"
                      className="bg-success/10 text-success border-success"
                    >
                      Excellent
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">
                      Pre-approved Limit
                    </span>
                    <span className="font-semibold text-foreground">
                      ₹5,00,000
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-3">
            <Card className="h-[calc(100vh-6rem)] flex flex-col text-base leading-relaxed">
              {/* Header */}
              <div className="p-6 border-b bg-gradient-primary text-white rounded-t-lg">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center">
                    <Bot className="h-7 w-7" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-xl">AI Loan Assistant</h2>
                    <p className="text-sm text-white/80">
                      Online • Ready to help
                    </p>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-8 space-y-5">
                {messages.map((message, idx) => (
                  <div
                    key={idx}
                    className={`flex gap-3 animate-fade-in ${
                      message.role === "user"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    {message.role === "assistant" && (
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Bot className="h-6 w-6 text-primary" />
                      </div>
                    )}
                    <div
                      className={`max-w-[75%] rounded-2xl px-5 py-4 whitespace-pre-line text-[1rem] ${
                        message.role === "user"
                          ? "bg-primary text-white"
                          : "bg-muted text-foreground"
                      }`}
                    >
                      <p className="leading-relaxed">{message.content}</p>
                      <p
                        className={`text-xs mt-2 ${
                          message.role === "user"
                            ? "text-white/70"
                            : "text-muted-foreground"
                        }`}
                      >
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                    {message.role === "user" && (
                      <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center shrink-0">
                        <User className="h-6 w-6 text-primary" />
                      </div>
                    )}
                  </div>
                ))}

                {isTyping && (
                  <div className="flex gap-3 animate-fade-in">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Bot className="h-6 w-6 text-primary" />
                    </div>
                    <div className="bg-muted rounded-2xl px-5 py-4">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-primary/60 animate-bounce"></div>
                        <div
                          className="w-2 h-2 rounded-full bg-primary/60 animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                        <div
                          className="w-2 h-2 rounded-full bg-primary/60 animate-bounce"
                          style={{ animationDelay: "0.4s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="p-6 border-t bg-muted/30">
                <div className="flex gap-4">
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Button
                    variant="outline"
                    size="lg"
                    className="shrink-0 px-5 py-3"
                    onClick={handleUploadClick}
                  >
                    <Upload className="h-5 w-5" />
                  </Button>
                  <Input
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSend()}
                    className="flex-1 text-base py-3 px-4"
                  />
                  <Button
                    onClick={handleSend}
                    size="lg"
                    className="shrink-0 px-5 py-3 text-base"
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
