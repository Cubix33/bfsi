import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
