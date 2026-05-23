import { Navigate, Route, Routes } from "react-router-dom";
import RoleRoute from "./auth/RoleRoute";
import { useAuth } from "./auth/AuthContext";
import Login from "./pages/Login";
import CustomerApp from "./pages/CustomerApp";
import SocDashboard from "./pages/SocDashboard";
import AlertDetails from "./pages/AlertDetails";
import AdminPanel from "./pages/AdminPanel";
import AccessDenied from "./pages/AccessDenied";

function HomeRedirect() {
  const { user, isAuthenticated, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-slate-950 p-8 text-white">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role === "CUSTOMER") return <Navigate to="/customer" replace />;
  return <Navigate to="/dashboard" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/customer"
        element={
          <RoleRoute allowedRoles={["CUSTOMER"]}>
            <CustomerApp />
          </RoleRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <RoleRoute allowedRoles={["ANALYST", "ADMIN"]}>
            <SocDashboard />
          </RoleRoute>
        }
      />
      <Route
        path="/alerts/:alertId"
        element={
          <RoleRoute allowedRoles={["ANALYST", "ADMIN"]}>
            <AlertDetails />
          </RoleRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <RoleRoute allowedRoles={["ADMIN"]}>
            <AdminPanel />
          </RoleRoute>
        }
      />
      <Route path="/denied" element={<AccessDenied />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

