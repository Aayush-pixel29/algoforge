import { NavLink, Route, Routes } from "react-router-dom";
import { LayoutDashboard, Zap, BookOpen, Library as LibraryIcon, Settings as SettingsIcon, Beaker } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Forge from "./pages/Forge";
import Study from "./pages/Study";
import Library from "./pages/Library";
import Settings from "./pages/Settings";
import Phase2 from "./pages/Phase2";

export default function App() {
  return (
    <div className="shell">
      <aside className="nav">
        <div className="brand">
          <Zap size={22} color="#fff" fill="#fff" />
          ALGOFORGE
        </div>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          <LayoutDashboard size={18} /> Mission Control
        </NavLink>
        <NavLink to="/forge" className={({ isActive }) => (isActive ? "active" : "")}>
          <Zap size={18} /> Forge Studio
        </NavLink>
        <NavLink to="/study" className={({ isActive }) => (isActive ? "active" : "")}>
          <BookOpen size={18} /> Study Deck
        </NavLink>
        <NavLink to="/library" className={({ isActive }) => (isActive ? "active" : "")}>
          <LibraryIcon size={18} /> Library
        </NavLink>
        <div style={{ margin: "1rem 0", height: "1px", background: "var(--line)" }}></div>
        <NavLink to="/phase2" className={({ isActive }) => (isActive ? "active" : "")}>
          <Beaker size={18} /> Phase 2 Sandbox
        </NavLink>
        <div style={{ flexGrow: 1 }}></div>
        <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>
          <SettingsIcon size={18} /> Settings
        </NavLink>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/forge" element={<Forge />} />
          <Route path="/study" element={<Study />} />
          <Route path="/study/:folder" element={<Study />} />
          <Route path="/library" element={<Library />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/phase2" element={<Phase2 />} />
        </Routes>
      </main>
    </div>
  );
}
