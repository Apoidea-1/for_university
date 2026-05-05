export type ImportanceLevel = "low" | "medium" | "high" | "strategic";
export type InteractionType = "meeting" | "message" | "call" | "project" | "other";
export type ReminderStatus = "active" | "completed";
export type ReminderType = "follow_up" | "congratulation" | "reconnect" | "custom";
export type IntegrationProvider = "google_calendar" | "linkedin" | "telegram";
export type IntegrationStatus = "connected" | "not_connected" | "coming_soon";

export interface User {
  id: number;
  full_name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Category {
  id: number;
  user_id: number | null;
  name: string;
  color: string;
  created_at: string;
}

export interface Tag {
  id: number;
  user_id: number | null;
  name: string;
  created_at: string;
}

export interface Contact {
  id: number;
  user_id: number;
  first_name: string;
  last_name: string | null;
  company: string | null;
  role: string | null;
  source_where_met: string | null;
  email: string | null;
  phone: string | null;
  telegram: string | null;
  linkedin: string | null;
  other_social: string | null;
  category_id: number | null;
  importance_level: ImportanceLevel;
  last_interaction_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  category: Category | null;
  tags: Tag[];
}

export interface ContactListResponse {
  total: number;
  items: Contact[];
}

export interface Interaction {
  id: number;
  contact_id: number;
  type: InteractionType;
  title: string;
  description: string | null;
  interaction_date: string;
  created_at: string;
}

export interface Reminder {
  id: number;
  contact_id: number | null;
  user_id: number;
  title: string;
  description: string | null;
  due_date: string;
  status: ReminderStatus;
  reminder_type: ReminderType;
  created_at: string;
  updated_at: string;
  contact: {
    id: number;
    first_name: string;
    last_name: string | null;
    company: string | null;
  } | null;
}

export interface ContactMetadataSuggestion {
  category: string;
  tags: string[];
  note_summary: string;
  next_action: string;
}

export interface NextActionSuggestion {
  next_action: string;
  rationale: string;
}

export interface AnalyticsOverview {
  new_contacts_7d: number;
  new_contacts_30d: number;
  interactions_7d: number;
  interactions_30d: number;
  active_reminders: number;
  overdue_reminders: number;
  stale_contacts_count: number;
  activity_timeline: Array<{
    date: string;
    contacts_added: number;
    interactions_logged: number;
  }>;
}

export interface CategoryAnalyticsItem {
  category_name: string;
  color: string;
  count: number;
}

export interface StaleContact {
  id: number;
  first_name: string;
  last_name: string | null;
  company: string | null;
  last_interaction_date: string | null;
  days_since_last_interaction: number | null;
}

export interface Integration {
  id: number;
  user_id: number;
  provider: IntegrationProvider;
  status: IntegrationStatus;
  metadata_json: Record<string, unknown>;
  created_at: string;
}
