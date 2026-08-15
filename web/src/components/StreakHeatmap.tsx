import { useEffect, useState } from "react";
import { api, StreakData } from "../api";
import { Flame } from "lucide-react";

export function StreakHeatmap() {
  const [data, setData] = useState<StreakData | null>(null);

  useEffect(() => {
    api<StreakData>("/api/streak")
      .then(setData)
      .catch((err) => console.error("Failed to load streak:", err));
  }, []);

  if (!data) return <div className="animate-pulse h-24 bg-gray-900 rounded-lg border border-gray-800"></div>;

  // Split calendar into weeks (7 days per column)
  const weeks: { date: string; active: boolean }[][] = [];
  let currentWeek: { date: string; active: boolean }[] = [];
  
  data.calendar.forEach((day, i) => {
    currentWeek.push(day);
    if (currentWeek.length === 7 || i === data.calendar.length - 1) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider flex items-center gap-2">
          <Flame className="w-4 h-4 text-orange-500" />
          Commit Streak
        </h3>
        <div className="flex gap-4 text-sm">
          <div className="flex flex-col items-end">
            <span className="text-gray-400 text-xs uppercase">Current</span>
            <span className="text-white font-bold">{data.current_streak} days</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-gray-400 text-xs uppercase">Longest</span>
            <span className="text-white font-bold">{data.longest_streak} days</span>
          </div>
        </div>
      </div>
      
      <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-thin">
        {weeks.map((week, i) => (
          <div key={i} className="flex flex-col gap-1">
            {week.map((day, j) => (
              <div
                key={day.date}
                title={`${day.date}: ${day.active ? 'Committed' : 'No commits'}`}
                className={`w-3 h-3 rounded-sm ${
                  day.active ? 'bg-orange-500 shadow-[0_0_4px_rgba(249,115,22,0.4)]' : 'bg-gray-800'
                }`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
