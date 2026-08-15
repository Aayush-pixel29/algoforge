import { useEffect, useState } from "react";
import { api, AppSettings } from "../api";
import { CalendarClock } from "lucide-react";

export function InterviewCountdown() {
  const [dateStr, setDateStr] = useState<string>("");

  useEffect(() => {
    api<AppSettings>("/api/settings")
      .then((s) => {
        if (s.interview_date) setDateStr(s.interview_date);
      })
      .catch((err) => console.error("Failed to load settings:", err));
  }, []);

  if (!dateStr) return null;

  const target = new Date(dateStr);
  const now = new Date();
  const diffTime = target.getTime() - now.getTime();
  
  if (diffTime <= 0) {
    return (
      <div className="bg-orange-950/30 border border-orange-900/50 rounded-lg p-4 flex items-center gap-3">
        <CalendarClock className="w-5 h-5 text-orange-500" />
        <span className="text-orange-200 font-medium">It's interview day! Good luck!</span>
      </div>
    );
  }
  
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex flex-col justify-between relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider flex items-center gap-2 mb-2 relative z-10">
        <CalendarClock className="w-4 h-4 text-orange-500" />
        Target Interview
      </h3>
      <div className="flex items-baseline gap-2 relative z-10">
        <span className="text-4xl font-bold text-white tracking-tighter">{diffDays}</span>
        <span className="text-gray-400 text-sm uppercase tracking-wider font-medium">Days left</span>
      </div>
    </div>
  );
}
