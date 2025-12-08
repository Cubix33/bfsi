import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Building2 } from "lucide-react";

const Navbar = () => {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;
  const [isSignedIn, setIsSignedIn] = useState(false);

  // Load sign-in state from localStorage when component mounts
  useEffect(() => {
    const storedState = localStorage.getItem("isSignedIn");
    if (storedState === "true") {
      setIsSignedIn(true);
    }
  }, []);

  // Handle sign-in click
  const handleSignIn = () => {
    setIsSignedIn(true);
    localStorage.setItem("isSignedIn", "true"); // persist
  };

  // Optional: logout/reset method (for future)
  const handleLogout = () => {
    setIsSignedIn(false);
    localStorage.removeItem("isSignedIn");
  };

  return (
    <nav className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b shadow-sm">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link
          to="/"
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
        >
          <Building2 className="h-7 w-7 text-primary" />
          <span className="font-bold text-xl text-primary">Tata Capital</span>
          <span className="font-normal text-lg text-foreground">SmartLoans</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link
            to="/"
            className={`text-sm font-medium transition-colors hover:text-primary ${
              isActive("/") ? "text-primary" : "text-muted-foreground"
            }`}
          >
            Home
          </Link>
          <Link
            to="/#about"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
          >
            About
          </Link>
          <Link
            to="/#how-it-works"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
          >
            How It Works
          </Link>
        </div>

               <div className="flex items-center gap-3">
          {!isSignedIn && (
            <Link to="/login" onClick={handleSignIn}>
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
          )}

          <Link to="/chat">
            <Button variant="hero" size="sm">
              Apply Now
            </Button>
          </Link>

          {/* NEW: Visit Profile (Dashboard) when logged in */}
          {isSignedIn && (
            <Link to="/dashboard">
              <Button
                variant="outline"
                size="sm"
                className="text-xs text-muted-foreground hover:text-primary"
              >
                Visit Profile
              </Button>
            </Link>
          )}

          {isSignedIn && (
            <Link to="/" onClick={handleLogout}>
              <Button
                variant="outline"
                size="sm"
                className="text-xs text-muted-foreground hover:text-primary"
              >
                Log Out
              </Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
