import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Send, Upload, Bot, User} from "lucide-react";
import Navbar from "@/components/Navbar";
import VoiceChat from "@/components/VoiceChat";
import { Languages } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const LANGUAGES = {
  en: { name: "English", flag: "🇬🇧" },
  hi: { name: "हिंदी", flag: "🇮🇳" },
  ta: { name: "தமிழ்", flag: "🇮🇳" },
  te: { name: "తెలుగు", flag: "🇮🇳" },
  bn: { name: "বাংলা", flag: "🇮🇳" },
  mr: { name: "मराठी", flag: "🇮🇳" },
  gu: { name: "ગુજરાતી", flag: "🇮🇳" },
};

type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

const Chat = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentStage, setCurrentStage] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [language, setLanguage] = useState("en");

  const stages = [
    "Initial",
    "Needs Assessment",
    "Verification",
    "Credit Check",
    "Underwriting",
    "Document Upload",
    "Approval",
  ];

  // Initialize session ID + first message
  useEffect(() => {
    let sid = localStorage.getItem("loan_session_id");
    if (!sid) {
      sid = crypto.randomUUID();
      localStorage.setItem("loan_session_id", sid);
    }
    setSessionId(sid);

    // Initial greeting
    setMessages([
      {
        role: "assistant",
        content: "Hello 👋 I'm your AI Loan Assistant from Tata Capital.\n\nTo get started, could you please share your registered phone number?",
        timestamp: new Date(),
      },
    ]);
  }, []);

  // 🚀 CALLS YOUR REAL PYTHON CHATBOT 
  const sendToBackend = async (text: string) => {
    if (!sessionId) return;
    setIsTyping(true);

    try {
      const res = await fetch(`/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          language: language,
        }),
      });
      const data = await res.json();

      if (data.error) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Sorry, something went wrong. Please try again.",
            timestamp: new Date(),
          },
        ]);
        setIsTyping(false);
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          timestamp: new Date(),
        },
      ]);

      const stageMap: Record<string, number> = {
        initial: 1,
        needs_assessment: 2,
        verification: 3,
        credit_check: 4,
        underwriting: 5,
        document_upload: 6,
        approval: 7,
        rejection: 7,
      };
      if (data.stage && stageMap[data.stage]) {
        setCurrentStage(stageMap[data.stage]);
      }
    } catch (err) {
      console.log(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Network error. Please check your connection.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const text = input.trim();

    const userMessage: Message = {
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // 🚀 SEND TO YOUR REAL PYTHON CHATBOT
    sendToBackend(text);
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const userMessage: Message = {
      role: "user",
      content: `📂 Uploaded file: ${file.name}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      // Create form data and upload file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId || '');

      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (data.success && data.reply) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.reply,
            timestamp: new Date(),
          },
        ]);
        
        if (data.stage) {
          const stageIndex = stages.findIndex(
            (s) => s.toLowerCase().replace(" ", "_") === data.stage
          );
          if (stageIndex !== -1) setCurrentStage(stageIndex + 1);
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, there was an error uploading your file. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
      // Allow selecting the same file again by clearing the input value
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleLanguageChange = async (newLang: string) => {
  setLanguage(newLang);
  
  // Clear and restart session
  const newSid = crypto.randomUUID();
  localStorage.setItem("loan_session_id", newSid);
  setSessionId(newSid);
  setMessages([]);
  setIsTyping(true);

  // Get greeting in new language
  try {
    const res = await fetch(`/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: newSid,
        message: "__INIT__",
        language: newLang,
      }),
    });
    const data = await res.json();
    setMessages([{
      role: "assistant",
      content: data.reply,
      timestamp: new Date(),
    }]);
  } catch (err) {
    console.log(err);
  } finally {
    setIsTyping(false);
  }
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

              {/* Static Credit Score Display to match UI design */}
              <div className="mt-6 pt-6 border-t">
                <div className="space-y-3 text-base">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Credit Score</span>
                    <Badge
                      variant="outline"
                      className="bg-success/10 text-success border-success"
                    >
                      Should be &gt;700 ideally 
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">
                      Pre-approved Limit
                    </span>
                    <span className="font-semibold text-foreground">
                      up to ₹10,00,000
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
              {/* Header */}
<div className="p-6 border-b bg-gradient-primary text-white rounded-t-lg">
  <div className="flex items-center justify-between">
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
    
    {/* Language Selector */}
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="bg-white/10 border-white/20 text-white hover:bg-white/20">
          <Languages className="mr-2 h-4 w-4" />
          {LANGUAGES[language].flag} {LANGUAGES[language].name}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuRadioGroup value={language} onValueChange={handleLanguageChange}>
          {Object.entries(LANGUAGES).map(([code, { name, flag }]) => (
            <DropdownMenuRadioItem key={code} value={code}>
              {flag} {name}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-8 space-y-5">
                {messages.map((message, idx) => (
                  <div
                    key={idx}
                    className={`flex gap-3 animate-fade-in ${
                      message.role === "user" ? "justify-end" : "justify-start"
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
                    aria-label="Upload document"
                    title="Upload document"
                  >
                    <Upload className="h-5 w-5" />
                  </Button>
                  <Input
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) =>
                      e.key === "Enter" && !e.shiftKey && handleSend()
                    }
                    className="flex-1 text-base py-3 px-4"
                  />
                  <Button
                    onClick={handleSend}
                    size="lg"
                    className="shrink-0 px-5 py-3 text-base"
                    disabled={!input.trim()}
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </div>

                {/* Voice Chat Integration - Free Browser APIs */}
                <div className="mt-4 pt-4 border-t">
                  <VoiceChat 
                    sessionId={sessionId} 
                    language={language}
                    onAddMessage={(role, content) => {
                      setMessages(prev => [...prev, { role, content, timestamp: new Date() }]);
                    }}
                  />
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