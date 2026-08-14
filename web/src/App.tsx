import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Forge from "./pages/Forge";
import Study from "./pages/Study";
import Library from "./pages/Library";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <div className="shell">
      <aside className="nav">
        <div className="brand">ALGOFORGE</div>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Dashboard</NavLink>
        <NavLink to="/forge" className={({ isActive }) => (isActive ? "active" : "")}>Forge</NavLink>
        <NavLink to="/study" className={({ isActive }) => (isActive ? "active" : "")}>Study</NavLink>
        <NavLink to="/library" className={({ isActive }) => (isActive ? "active" : "")}>Library</NavLink>
        <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>Settings</NavLink>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/forge" element={<Forge />} />
          <Route path="/study" element={<Study />} />
          <Route path="/study/:folder" element={<Study />} />
          <Route path="/library" element={<Library />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
