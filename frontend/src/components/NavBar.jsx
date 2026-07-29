import React from "react";
import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }) =>
  `rounded px-3 py-1.5 text-sm font-medium ${
    isActive ? "bg-surface-raised text-slate-100" : "text-slate-400 hover:text-slate-200"
  }`;

export default function NavBar() {
  return (
    <nav className="flex items-center gap-2 border-b border-surface-border bg-surface px-6 py-3">
      <span className="mr-4 font-mono text-lg font-bold text-slate-100">ThreatGPT</span>
      <NavLink to="/" end className={linkClass}>
        Analyze
      </NavLink>
      <NavLink to="/alerts" className={linkClass}>
        Alerts
      </NavLink>
    </nav>
  );
}
