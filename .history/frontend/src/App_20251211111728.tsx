import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { MessageCircle } from "lucide-react";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import Summary from "./pages/Summary";
import Verification from "./pages/Verification";
import Results from "./pages/Results";
import Upload from "./pages/Upload";
import Approval from "./pages/Approval";
import Dashboard from "./pages/Dashboard";
import SanctionLetter from "./pages/SanctionLetter";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./routes/ProtectedRoute";

const queryClient = new QueryClient();

// your WhatsApp URL
const WHATSAPP_URL = "https://wa.me/14155238886?text=Hi%20Tata%20Capital";

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/chat" element={<Chat />} />
            <Route path="/summary" element={<Summary />} />
            <Route path="/verify" element={<Verification />} />
            <Route path="/results" element={<Results />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/approval" element={<Approval />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/sanction-letter/:id" element={<SanctionLetter />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>

      {/* floating WhatsApp button */}
      <div className="fixed bottom-4 right-4 z-50">
        <a href={WHATSAPP_URL} target="_blank" rel="noreferrer">
          <Button
            size="icon"
            className="h-14 w-14 rounded-full bg-[#25D366] hover:bg-[#1ebe57] shadow-lg flex items-center justify-center"
            aria-label="Chat with us on WhatsApp"
          >
            <MessageCircle className="h-7 w-7 text-white" />
          </Button>
        </a>
      </div>

    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
