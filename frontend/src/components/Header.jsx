import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

const today = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  year: "numeric",
  month: "long",
  day: "numeric",
});

export default function Header() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="masthead container">
      <div className="masthead-top">
        <span className="label date">{today}</span>
        <span className="label">{user ? user.email : "Reader's edition"}</span>
      </div>
      <NavLink to="/" className="masthead-title">
        Sarca<em>Sense</em>
      </NavLink>
      <nav>
        <NavLink to="/" end>Analyze</NavLink>
        {!loading && user && (
          <>
            <NavLink to="/history">History</NavLink>
            <NavLink to="/account">Account</NavLink>
            <button
              onClick={async () => {
                await logout();
                navigate("/");
              }}
            >
              Sign out
            </button>
          </>
        )}
        {!loading && !user && (
          <>
            <NavLink to="/login">Sign in</NavLink>
            <NavLink to="/register">Subscribe</NavLink>
          </>
        )}
      </nav>
    </header>
  );
}
