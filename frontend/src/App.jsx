import React from "react";
import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import AnalyzePage from "./pages/AnalyzePage";
import AlertsListPage from "./pages/AlertsListPage";
import AlertDetailPage from "./pages/AlertDetailPage";

export default function App() {
  return (
    <div className="min-h-screen bg-surface text-slate-100">
      <NavBar />
      <main className="p-6">
        <Routes>
          <Route path="/" element={<AnalyzePage />} />
          <Route path="/alerts" element={<AlertsListPage />} />
          <Route path="/alerts/:id" element={<AlertDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
