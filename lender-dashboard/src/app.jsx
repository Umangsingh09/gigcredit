import { useState } from "react";

import Layout from "./components/Layout";
import Dashboard from "../pages/Dashboard";
import Applications from "../pages/Applications";
import WorkerProfile from "../pages/WorkerProfile";

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const [selectedApplication, setSelectedApplication] = useState(null);

  const handleReview = (application) => {
    setSelectedApplication(application);
    setCurrentPage("worker-profile");
  };

  const handleNavigate = (page) => {
    setCurrentPage(page);
  };

  return (
    <Layout
      currentPage={currentPage}
      onNavigate={handleNavigate}
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
    </Layout>
  );
}

export default App;