import { Navigate } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { useAuth } from "./AuthContext";

export default function RoleRoute({ allowedRoles, children }) {
  const { user } = useAuth();

  return (
    <ProtectedRoute>
      {user && allowedRoles.includes(user.role) ? children : <Navigate to="/denied" replace />}
    </ProtectedRoute>
  );
}

