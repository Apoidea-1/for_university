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

export interface AiReminderSuggestion {
  contact_id: number;
  title: string;
  due_in_days: number;
  priority: "high" | "medium" | "low";
  reminder_type: ReminderType;
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

export interface ContactStrategy {
  source: "heuristic" | "remote";
  summary: string;
  recommended_channel: string;
  next_action: string;
  meeting_goal: string;
  meeting_window: string;
  agenda: string[];
  message_draft: string;
  risk_flags: string[];
}

export interface BusinessCardScanResult {
  source: "remote";
  full_name: string | null;
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  role: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  telegram: string | null;
  linkedin: string | null;
  notes: string | null;
  tags: string[] | null;
  confidence: number | null;
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

export interface ContactPreview {
  id: number;
  full_name: string;
  first_name: string;
  last_name: string | null;
  company: string | null;
  role: string | null;
  importance_level: ImportanceLevel;
  status: "active" | "target" | "dormant";
}

export interface ContactRelationship {
  id: number;
  user_id: number;
  source_contact: ContactPreview;
  target_contact: ContactPreview;
  relationship_type: string;
  strength: number;
  shared_context: string | null;
  notes: string | null;
  last_active_at: string | null;
  message_count: number;
  interaction_count: number;
  is_bridge: boolean;
  pair_key: string;
}

export interface NetworkGraphNode {
  id: number | "user";
  label: string;
  status: "active" | "target" | "dormant" | "self";
  color: string;
  size: number;
  degree: number;
  is_bridge: boolean;
  importance_level?: ImportanceLevel;
  company?: string | null;
  category_name?: string | null;
}

export interface NetworkGraphLink {
  source: number | "user";
  target: number | "user";
  weight: number;
  kind: string;
  pair_key?: string;
}

export interface NetworkGraphSummary {
  total_contacts: number;
  total_relationships: number;
  active_contacts: number;
  target_contacts: number;
  dormant_contacts: number;
  bridge_contacts: number;
  bridge_names: string[];
}

export interface NetworkGraphData {
  nodes: NetworkGraphNode[];
  links: NetworkGraphLink[];
  summary: NetworkGraphSummary;
}

export interface ContactMessage {
  id: number;
  pair_key: string;
  sender_contact: ContactPreview;
  recipient_contact: ContactPreview;
  body: string;
  message_type: "chat" | "note" | "follow_up" | "meeting";
  sent_at: string;
  metadata_json: Record<string, unknown>;
  is_ai_draft: boolean;
}

export interface ConversationSummary {
  pair_key: string;
  participants: ContactPreview[];
  last_message: ContactMessage;
  message_count: number;
  relationship: ContactRelationship | null;
}

export interface Integration {
  id: number;
  user_id: number;
  provider: IntegrationProvider;
  status: IntegrationStatus;
  metadata_json: Record<string, unknown>;
  created_at: string;
}
