import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import CadastroPage from "./pages/CadastroPage";
import ContaPage from "./pages/ContaPage";
import DepositoPage from "./pages/DepositoPage";
import HistoricoPage from "./pages/HistoricoPage";
import LimitePage from "./pages/LimitePage";
import LoginPage from "./pages/LoginPage";
import SaquePage from "./pages/SaquePage";
import TransferenciaPage from "./pages/TransferenciaPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/cadastro" element={<CadastroPage />} />
        <Route
          path="/conta"
          element={
            <ProtectedRoute>
              <ContaPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/depositar"
          element={
            <ProtectedRoute>
              <DepositoPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/sacar"
          element={
            <ProtectedRoute>
              <SaquePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/transferir"
          element={
            <ProtectedRoute>
              <TransferenciaPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/historico"
          element={
            <ProtectedRoute>
              <HistoricoPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/limite"
          element={
            <ProtectedRoute>
              <LimitePage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}
