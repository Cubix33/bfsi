import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Building2 } from "lucide-react";

import { auth } from "@/firebase/firebaseConfig";
import { onAuthStateChanged, signOut } from "firebase/auth";

const Navbar = () => {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;

  const [isSignedIn, setIsSignedIn] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setIsSignedIn(!!user); // true if logged in, false if not
    });

    return () => unsubscribe();
  }, []);

  const handleLogout = async () => {
    await signOut(auth);
    setIsSignedIn(false);
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
          <a
            href="/#about"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
          >
            About
          </a>
          <a
            href="/#how-it-works"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
          >
            How It Works
          </a>
        </div>

        <div className="flex items-center gap-3">
          {!isSignedIn && (
            <Link to="/login">
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
            <Button
              onClick={handleLogout}
              variant="outline"
              size="sm"
              className="text-xs text-muted-foreground hover:text-primary"
            >
              Log Out
            </Button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
