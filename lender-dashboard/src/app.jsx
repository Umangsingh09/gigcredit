import { useState } from "react";

import Layout from "./components/Layout";
import Login from "../pages/Login";
import Dashboard from "../pages/Dashboard";
import Applications from "../pages/Applications";
import WorkerProfile from "../pages/WorkerProfile";
import Analytics from "../pages/Analytics";
import Settings from "../pages/Settings";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(localStorage.getItem("gigcredit_access_token")));
  const [profile, setProfile] = useState(() => JSON.parse(localStorage.getItem("gigcredit_profile") || "null"));
  const [currentPage, setCurrentPage] = useState("dashboard");

  const [selectedApplication, setSelectedApplication] = useState(null);

  const handleReview = (application) => {
    setSelectedApplication(application);
    setCurrentPage("worker-profile");
  };

  const handleNavigate = (page) => {
    setCurrentPage(page);
  };

  const handleAuthenticated = (response) => {
    localStorage.setItem("gigcredit_access_token", response.access_token);
    localStorage.setItem("gigcredit_profile", JSON.stringify(response));
    setProfile(response);
    setIsAuthenticated(true);
    setCurrentPage("dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("gigcredit_access_token");
    localStorage.removeItem("gigcredit_profile");
    setIsAuthenticated(false);
    setCurrentPage("dashboard");
  };

  if (!isAuthenticated) {
    return <Login onAuthenticated={handleAuthenticated} />;
  }

  return (
    <Layout
      currentPage={currentPage}
      onNavigate={handleNavigate}
      onLogout={handleLogout}
      profile={profile}
    >
      {currentPage === "dashboard" && (
        <Dashboard onNavigate={handleNavigate} />
      )}

      {currentPage === "applications" && (
        <Applications onReview={handleReview} />
      )}

      {currentPage === "worker-profile" && selectedApplication && (
        <WorkerProfile
          application={selectedApplication}
          onBack={() => setCurrentPage("applications")}
        />
      )}

      {currentPage === "analytics" && <Analytics />}

      {currentPage === "settings" && <Settings />}
    </Layout>
  );
}

export default App;