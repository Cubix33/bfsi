import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, FileText, TrendingUp, Clock, MessageCircle } from "lucide-react";
import Navbar from "@/components/Navbar";

const Dashboard = () => {
  const activeApplications = [
    {
      id: "TCSL2025001234",
      customerName: "Riya Sharma",
      amount: 500000,
      status: "Approved",
      date: "2025-01-15",
    },
    {
      id: "TCSL2025001120",
      customerName: "Riya Sharma",
      amount: 300000,
      status: "Under Review",
      date: "2025-01-10",
    },
  ];

  const pastApplications = [
    {
      id: "TCSL2024005678",
      customerName: "Riya Sharma",
      amount: 200000,
      status: "Disbursed",
      date: "2024-12-05",
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Approved":
        return "bg-success/10 text-success border-success";
      case "Under Review":
        return "bg-warning/10 text-warning border-warning";
      case "Disbursed":
        return "bg-primary/10 text-primary border-primary";
      default:
        return "bg-muted/10 text-muted-foreground border-muted";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <Navbar />

      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8 animate-fade-in">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Welcome Back, Riya!</h1>
            <p className="text-lg text-muted-foreground">
              Manage your loan applications and track your progress
            </p>
          </div>
          <Link to="/chat">
            <Button variant="hero" size="lg">
              <Plus className="mr-2 h-5 w-5" />
              New Application
            </Button>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card className="border-2 hover:shadow-lg transition-all animate-scale-in">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Loans
              </CardTitle>
              <FileText className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-primary">2</div>
              <p className="text-xs text-muted-foreground mt-1">Currently processing</p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:shadow-lg transition-all animate-scale-in" style={{ animationDelay: "100ms" }}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Disbursed
              </CardTitle>
              <TrendingUp className="h-5 w-5 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-success">₹8,00,000</div>
              <p className="text-xs text-muted-foreground mt-1">Lifetime amount</p>
            </CardContent>
          </Card>

          <Card className="border-2 hover:shadow-lg transition-all animate-scale-in" style={{ animationDelay: "200ms" }}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Credit Score
              </CardTitle>
              <Clock className="h-5 w-5 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">782</div>
              <p className="text-xs text-muted-foreground mt-1">Excellent rating</p>
            </CardContent>
          </Card>
        </div>

        {/* Active Applications */}
        <Card className="border-2 shadow-lg mb-8 animate-fade-in-up">
          <CardHeader className="bg-gradient-primary text-white rounded-t-lg">
            <CardTitle className="text-2xl">Active Applications</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Application ID</TableHead>
                  <TableHead>Customer Name</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeApplications.map((app) => (
                  <TableRow key={app.id}>
                    <TableCell className="font-medium">{app.id}</TableCell>
                    <TableCell>{app.customerName}</TableCell>
                    <TableCell className="font-semibold">
                      ₹{app.amount.toLocaleString("en-IN")}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getStatusColor(app.status)}>
                        {app.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{new Date(app.date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      {app.status === "Approved" ? (
                        <Link to="/approval">
                          <Button variant="outline" size="sm">
                            View Letter
                          </Button>
                        </Link>
                      ) : (
                        <Link to="/chat">
                          <Button variant="outline" size="sm">
                            Continue
                          </Button>
                        </Link>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Past Applications */}
        <Card className="border-2 shadow-lg animate-fade-in-up" style={{ animationDelay: "100ms" }}>
          <CardHeader>
            <CardTitle className="text-2xl text-foreground">Past Applications</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Application ID</TableHead>
                  <TableHead>Customer Name</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pastApplications.map((app) => (
                  <TableRow key={app.id}>
                    <TableCell className="font-medium">{app.id}</TableCell>
                    <TableCell>{app.customerName}</TableCell>
                    <TableCell className="font-semibold">
                      ₹{app.amount.toLocaleString("en-IN")}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getStatusColor(app.status)}>
                        {app.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{new Date(app.date).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* WhatsApp CTA to talk to the same loan assistant over WhatsApp (Twilio number) */}
        <div className="mt-8 flex justify-end">
          <a
            href="https://wa.me/14787778556?text=Hi%20Tata%20Capital"
            target="_blank"
            rel="noreferrer"
          >
            <Button
              variant="outline"
              size="lg"
              className="flex items-center gap-2 border-[#25D366] text-[#25D366] hover:bg-[#25D366]/10"
            >
              <MessageCircle className="h-5 w-5" />
              Chat on WhatsApp
            </Button>
          </a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
