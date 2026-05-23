import { Link, NavLink } from "react-router-dom";
import { LogOut, ShieldCheck } from "lucide-react";
import { useAuth } from "../auth/AuthContext";

export default function Navbar({ variant = "dark" }) {
  const { user, logout } = useAuth();
  const dark = variant === "dark";
  const linkClass = ({ isActive }) =>
    `rounded-md px-3 py-2 text-sm font-medium transition ${
      isActive
        ? dark
          ? "bg-sky-500/15 text-sky-200"
          : "bg-slate-900 text-white"
        : dark
          ? "text-slate-300 hover:bg-white/5"
          : "text-slate-600 hover:bg-slate-100"
    }`;

  return (
    <header className={dark ? "border-b border-white/10 bg-slate-950/90" : "border-b border-slate-200 bg-white"}>
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link to="/" className={`flex items-center gap-2 font-bold ${dark ? "text-white" : "text-slate-950"}`}>
          <ShieldCheck className="h-6 w-6 text-sky-400" />
          AEGIS
        </Link>
        <nav className="flex items-center gap-2">
          {user?.role === "CUSTOMER" && <NavLink className={linkClass} to="/customer">Customer</NavLink>}
          {user && <NavLink className={linkClass} to="/messages">Verified Messages</NavLink>}
          {(user?.role === "ANALYST" || user?.role === "ADMIN") && <NavLink className={linkClass} to="/dashboard">SOC</NavLink>}
          {(user?.role === "ANALYST" || user?.role === "ADMIN") && <NavLink className={linkClass} to="/brand-protection">Brand Protection</NavLink>}
          {(user?.role === "ANALYST" || user?.role === "ADMIN") && <NavLink className={linkClass} to="/risk-transparency">Risk Transparency</NavLink>}
          {user?.role === "ADMIN" && <NavLink className={linkClass} to="/admin">Admin</NavLink>}
          <span className={`hidden text-sm sm:inline ${dark ? "text-slate-400" : "text-slate-500"}`}>{user?.name}</span>
          <button
            onClick={logout}
            className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
              dark ? "bg-white/10 text-white hover:bg-white/15" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </nav>
      </div>
    </header>
  );
}
