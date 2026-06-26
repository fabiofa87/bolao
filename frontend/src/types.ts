export type User = {
  id: number;
  email: string;
  display_name: string;
};

export type Team = {
  id: number;
  name: string;
  short_name: string;
  code: string;
  crest_url: string;
};

export type Prediction = {
  id: number;
  user: number;
  user_name: string;
  home_score: number;
  away_score: number;
  points: number;
  submitted_at: string;
  updated_at: string;
};

export type Match = {
  id: number;
  provider_id: number | null;
  stage: string;
  group: string;
  matchday: number | null;
  kickoff_at: string;
  lock_at: string;
  is_locked: boolean;
  status: string;
  home_team: Team;
  away_team: Team;
  scoring_home: number | null;
  scoring_away: number | null;
  penalties_home: number | null;
  penalties_away: number | null;
  my_prediction: Prediction | null;
  predictions: Prediction[];
};

export type RankingRow = {
  user_id: number;
  display_name: string;
  prediction_points: number;
  adjustment_points: number;
  correct_result_hits: number;
  total_points: number;
  rank: number;
};

export type PoolGroup = {
  id: number;
  name: string;
  slug: string;
};

export type ChatMessage = {
  id: number;
  pool_group: number;
  user: number;
  user_name: string;
  body: string;
  chat_date: string;
  created_at: string;
};

export type DailyChat = {
  groups: PoolGroup[];
  selected_group: PoolGroup | null;
  chat_date: string;
  messages: ChatMessage[];
};

