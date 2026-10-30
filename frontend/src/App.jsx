import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Header from "./components/Header";
import Analyze from "./pages/Analyze";
import Account from "./pages/Account";
import AuthForm from "./pages/AuthForm";
import History from "./pages/History";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="muted">Loading…</p>;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const location = useLocation();
  return (
    <>
      <Header />
      <main className="container">
        {/* keyed on the path so every navigation replays the entrance animation */}
        <div className="page" key={location.pathname}>
          <Routes location={location}>
            <Route path="/" element={<Analyze />} />
            <Route path="/login" element={<AuthForm mode="login" />} />
            <Route path="/register" element={<AuthForm mode="register" />} />
            <Route path="/history" element={<RequireAuth><History /></RequireAuth>} />
            <Route path="/account" element={<RequireAuth><Account /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
      <footer className="container">
        <div className="colophon label">
          trained on 28k news headlines (
          <a
            href="https://www.kaggle.com/datasets/rmisra/news-headlines-dataset-for-sarcasm-detection"
            target="_blank"
            rel="noopener noreferrer"
          >
            Kaggle dataset
          </a>
          ) · about 87% accurate · it can be wrong
        </div>
      </footer>
    </>
  );
}
