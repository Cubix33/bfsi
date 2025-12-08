import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MessageCircle, Zap, FileText, CheckCircle, ArrowRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import heroImage from "@/assets/hero-banking.jpg";

const Landing = () => {
  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-hero text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] animate-pulse-glow"></div>
        </div>
        <div className="container mx-auto px-4 py-20 relative">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-in-up">
              <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
                Get Instant Personal Loans with AI Assistance
              </h1>
              <p className="text-xl mb-8 text-white/90 leading-relaxed">
                Chat with our AI assistant to check your eligibility and download your sanction
                letter in minutes. Fast, secure, and hassle-free.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/login">
                  <Button size="lg" variant="hero" className="bg-white text-primary hover:bg-white/90">
                    Start Application <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <Link to="/login">
                  <Button size="lg" variant="outline" className="border-white text-primary hover:text-white hover:bg-white/10">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
            <div className="animate-scale-in hidden md:block">
              <img
                src={heroImage}
                alt="AI Banking Assistant"
                className="rounded-2xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 container mx-auto px-4">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="text-4xl font-bold text-foreground mb-4">Why Choose SmartLoans?</h2>
          <p className="text-xl text-muted-foreground">Experience the future of personal lending</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: MessageCircle,
              title: "Conversational Loan Chatbot",
              description:
                "Our AI assistant guides you through the entire process with natural conversation. No complex forms, just chat.",
            },
            {
              icon: Zap,
              title: "Instant Pre-Approval",
              description:
                "Get pre-approved in minutes with our advanced credit assessment system powered by AI and real-time data.",
            },
            {
              icon: FileText,
              title: "Auto-generated Sanction Letter",
              description:
                "Receive your official sanction letter instantly upon approval. Download and share digitally anytime.",
            },
          ].map((feature, idx) => (
            <Card
              key={idx}
              className="border-2 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 animate-fade-in-up bg-card"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              <CardContent className="pt-8 pb-8 text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-6">
                  <feature.icon className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-3 text-card-foreground">{feature.title}</h3>
                <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 bg-accent/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fade-in">
            <h2 className="text-4xl font-bold text-foreground mb-4">How It Works</h2>
            <p className="text-xl text-muted-foreground">
              Get your loan in 4 simple steps
            </p>
          </div>

          <div className="relative max-w-4xl mx-auto">
            <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-primary/20 -translate-x-1/2 hidden md:block"></div>

            {[
              {
                step: "1",
                title: "Start Chat",
                description:
                  "Begin a conversation with our AI assistant. Share your loan requirements and personal details.",
              },
              {
                step: "2",
                title: "Verify Identity",
                description:
                  "Complete quick KYC verification with OTP and document validation for security.",
              },
              {
                step: "3",
                title: "Upload Documents",
                description:
                  "Upload your salary slip and any additional documents requested by the system.",
              },
              {
                step: "4",
                title: "Get Approved",
                description:
                  "Receive instant decision and download your sanction letter immediately upon approval.",
              },
            ].map((item, idx) => (
              <div
                key={idx}
                className={`relative flex items-center gap-8 mb-12 animate-fade-in-up ${
                  idx % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"
                }`}
                style={{ animationDelay: `${idx * 150}ms` }}
              >
                <div className="flex-1">
                  <Card className="border-2 hover:shadow-lg transition-all duration-300">
                    <CardContent className="p-6">
                      <h3 className="text-2xl font-bold text-primary mb-2">{item.title}</h3>
                      <p className="text-muted-foreground leading-relaxed">{item.description}</p>
                    </CardContent>
                  </Card>
                </div>

                <div className="w-16 h-16 rounded-full bg-primary text-white flex items-center justify-center text-2xl font-bold shadow-lg z-10 shrink-0">
                  {item.step}
                </div>

                <div className="flex-1 hidden md:block"></div>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link to="/chat">
              <Button size="lg" variant="hero">
                Start Your Application <ArrowRight className="ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-foreground mb-4">What Our Customers Say</h2>
          <p className="text-xl text-muted-foreground">Trusted by thousands across India</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              name: "Priya Sharma",
              role: "Software Engineer",
              content:
                "The AI chatbot made the entire process so simple! I got approved in under 20 minutes.",
              rating: 5,
            },
            {
              name: "Rajesh Kumar",
              role: "Business Owner",
              content:
                "Best loan experience ever. No paperwork hassle, everything was digital and instant.",
              rating: 5,
            },
            {
              name: "Anita Patel",
              role: "Teacher",
              content:
                "I was skeptical at first, but the AI assistant was very helpful and patient with all my questions.",
              rating: 5,
            },
          ].map((testimonial, idx) => (
            <Card key={idx} className="border-2 hover:shadow-lg transition-all duration-300 animate-fade-in-up" style={{ animationDelay: `${idx * 100}ms` }}>
              <CardContent className="p-6">
                <div className="flex gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <CheckCircle key={i} className="h-5 w-5 text-success fill-success" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-4 italic leading-relaxed">
                  "{testimonial.content}"
                </p>
                <div>
                  <p className="font-semibold text-foreground">{testimonial.name}</p>
                  <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-foreground text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="font-bold text-lg mb-4">Tata Capital SmartLoans</h3>
              <p className="text-white/70 text-sm">
                AI-powered personal loans for the modern India.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Quick Links</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li>
                  <Link to="/" className="hover:text-white transition-colors">
                    Home
                  </Link>
                </li>
                <li>
                  <Link to="/login" className="hover:text-white transition-colors">
                    Login
                  </Link>
                </li>
                <li>
                  <Link to="/register" className="hover:text-white transition-colors">
                    Register
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li>Help Center</li>
                <li>Contact Us</li>
                <li>Privacy Policy</li>
                <li>Terms & Conditions</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Connect</h4>
              <p className="text-sm text-white/70 mb-2">Email: support@tatasmartloans.com</p>
              <p className="text-sm text-white/70">Phone: 1800-XXX-XXXX</p>
            </div>
          </div>
          <div className="border-t border-white/20 mt-8 pt-8 text-center text-sm text-white/70">
            © 2025 Tata Capital SmartLoans. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
