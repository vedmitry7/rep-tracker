export type Identity = { provider: string; external_id: string };

export type Exercise = {
  id: number;
  name: string;
  position: number;
  is_archived: boolean;
  weekly_report_enabled: boolean;
  created_at: string;
};

export type ExerciseEntry = {
  id: number;
  exercise_id: number;
  reps: number[];
  performed_on: string;
  created_at: string;
};

export type ExerciseStats = {
  total_reps: number;
  today_reps: number;
  last_7_days_reps: number;
  last_30_days_reps: number;
  all_time_entries: number;
  active_days: number;
  best_day: { date: string; reps: number } | null;
  last_entry: ExerciseEntry | null;
  today: string;
};

export type HistoryDay = { date: string; total_reps: number; entries_count: number };

export type Settings = {
  timezone: string;
  today: string;
  language: "en" | "ru" | "es" | "pt" | "tr" | "uk" | "id" | "hi" | "kk" | "pl" | "fr";
};
