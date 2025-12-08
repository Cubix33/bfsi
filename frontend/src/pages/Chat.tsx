// Chat.tsx - INTEGRATED WITH YOUR REAL PYTHON CHATBOT
import { useState, useRef, useEffect } from "react";
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

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentStage, setCurrentStage] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);

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
        }),
      });
      const data = await res.json();

      if (data.error) {
        setMessages(prev => [
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

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          timestamp: new Date(),
        },
      ]);

      // Update UI stages from backend state
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
      setMessages(prev => [
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
    setMessages(prev => [...prev, userMessage]);
    setInput("");

    // 🚀 SEND TO YOUR REAL PYTHON CHATBOT
    sendToBackend(text);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const userMessage: Message = {
      role: "user",
      content: `📂 Uploaded file: ${file.name}`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Tell backend about the upload
    sendToBackend(`I have uploaded my salary slip: ${file.name}`);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <Navbar />
      <div className="flex max-w-6xl mx-auto pt-20 pb-10 gap-6">
        {/* Sidebar - Stages */}
        <Card className="w-64 h-[600px] bg-slate-900 border-slate-800 flex flex-col">
          <div className="p-4 border-b border-slate-800">
            <h2 className="font-semibold text-lg mb-1">Application Stages</h2>
            <p className="text-xs text-slate-400">Track your journey in real time</p>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {stages.map((stage, idx) => (
              <div
                key={stage}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs ${
                  idx + 1 === currentStage
                    ? "bg-sky-500/10 text-sky-400 border border-sky-500/40"
                    : idx + 1 < currentStage
                    ? "bg-emerald-500/5 text-emerald-400 border border-emerald-500/30"
                    : "bg-slate-800/60 text-slate-400 border border-slate-800"
                }`}
              >
                <span className="font-medium">{idx + 1}. {stage}</span>
                <Badge
                  variant="outline"
                  className={
                    idx + 1 === currentStage
                      ? "border-sky-500/60 text-sky-300"
                      : idx + 1 < currentStage
                      ? "border-emerald-500/60 text-emerald-300"
                      : "border-slate-600 text-slate-400"
                  }
                >
                  {idx + 1 < currentStage
                    ? "Done"
                    : idx + 1 === currentStage
                    ? "In Progress"
                    : "Pending"}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        {/* Main Chat Area */}
        <Card className="flex-1 flex flex-col h-[600px] bg-slate-900 border-slate-800">
          {/* Header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-sky-500 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-semibold text-base">AI Loan Assistant</h2>
                <p className="text-xs text-slate-400">Online • Ready to help</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex ${
                  message.role === "assistant"
                    ? "items-start"
                    : "items-end justify-end"
                } gap-2`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-sky-500 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm whitespace-pre-line ${
                    message.role === "assistant"
                      ? "bg-slate-800 text-slate-50"
                      : "bg-sky-500 text-white"
                  }`}
                >
                  {message.content}
                  <div className="text-[10px] opacity-60 mt-1">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
                {message.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce delay-100" />
                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce delay-200" />
                <span>Assistant is typing…</span>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-slate-800 p-3 flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileSelect}
              accept=".pdf"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleUploadClick}
              className="border-slate-700 text-slate-300"
            >
              <Upload className="w-4 h-4" />
            </Button>
            <Input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder="Type your message..."
              className="flex-1 text-base py-3 px-4"
            />
            <Button onClick={handleSend} disabled={!input.trim()}>
              <Send className="w-4 h-4 mr-1" />
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Chat;
