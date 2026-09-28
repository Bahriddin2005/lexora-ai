// Mirrors backend/app/schemas/entry.py and the API responses in docs/04-api-spec.md.

export type Link = { text: string; slug: string | null };
export type TranslationOut = Link & { is_primary: boolean; note: string | null };

export type Sense = {
  id: number;
  pos: string;
  domain: string | null;
  register: string;
  cefr_level: string | null;
  definitions: Record<string, string>;
  translations: Record<string, TranslationOut[]>;
  examples: { text: string; translations: Record<string, string> }[];
  synonyms: Link[];
  antonyms: Link[];
};

export type WordEntry = {
  id: number;
  language_code: string;
  lemma: string;
  slug: string;
  entry_type: string;
  status: ContentStatus;
  confidence: number | null;
  cefr_level: string | null;
  frequency_zipf: number | null;
  tags: string[];
  etymology: Record<string, string> | null;
  audio_url: string | null;
  pronunciations: { ipa: string | null; accent: string | null; audio_url: string | null }[];
  forms: { form: string; tags: string[] }[];
  senses: Sense[];
  relations: Record<"synonym" | "antonym" | "related" | "derived" | "phrase", Link[]>;
  sources: { name: string; url: string | null; license: string | null }[];
  is_favorite: boolean;
  version: number;
  updated_at: string;
};

export type ContentStatus = "draft" | "ai_generated" | "published" | "rejected";

export type WordSummary = {
  id: number;
  language_code: string;
  lemma: string;
  slug: string;
  entry_type: string;
  status: ContentStatus;
  confidence: number | null;
  pos: string[];
  cefr_level: string | null;
  short_definition: string | null;
  primary_translation: { language_code: string; text: string } | null;
  match: "exact" | "form" | "reverse" | "prefix" | "list" | null;
  score: number | null;
  saved_at: string | null;
};

export type Intent = {
  type: "lookup" | "translate" | "list_new_terms";
  term: string | null;
  source_lang: string | null;
  target_lang: string | null;
  domain: string | null;
  year: number | null;
};

export type Job = {
  id: string;
  status: "queued" | "running" | "done" | "draft" | "rejected" | "not_a_word" | "failed";
  term: string | null;
  word: { language_code: string; slug: string } | null;
  message: string | null;
  suggestions: string[];
};

export type SearchResponse = {
  query: string;
  intent: Intent;
  results: WordSummary[];
  did_you_mean: { language_code: string; lemma: string; slug: string; score: number }[];
  job: Job | null;
  notice: string | null;
  ai_available: boolean;
};

export type Language = {
  code: string;
  name: string;
  native_name: string;
  script: string;
  direction: string;
  flag: string | null;
  tts_supported: boolean;
};

export type User = {
  id: string;
  email: string;
  display_name: string | null;
  role: "user" | "editor" | "admin";
  plan: "free" | "pro";
  ui_language: string;
  created_at: string;
};

export type TranslateResult = {
  translation: string;
  detected_source: string | null;
  alternatives: string[];
  notes: string | null;
  dictionary: { language_code: string; slug: string; lemma: string } | null;
  cached: boolean;
};

// ----- editor input (WordEntryIn) -----
export type TranslationIn = { text: string; is_primary: boolean; note: string | null };
export type SenseIn = {
  pos: string;
  domain: string | null;
  register: string;
  cefr_level: string | null;
  definitions: Record<string, string>;
  translations: Record<string, TranslationIn[]>;
  examples: { text: string; translations: Record<string, string> }[];
  synonyms: string[];
  antonyms: string[];
};
export type WordEntryIn = {
  lemma: string;
  entry_type: string;
  cefr_level: string | null;
  frequency_zipf: number | null;
  tags: string[];
  etymology: Record<string, string> | null;
  pronunciations: { ipa: string | null; accent: string | null }[];
  forms: { form: string; tags: string[] }[];
  senses: SenseIn[];
  relations: Partial<Record<"synonym" | "antonym" | "related" | "derived" | "phrase", string[]>>;
};

export type Page<T> = { items: T[]; total: number; page: number; size: number };

export type AdminWordRow = {
  id: number;
  language_code: string;
  lemma: string;
  slug: string;
  entry_type: string;
  status: ContentStatus;
  confidence: number | null;
  version: number;
  pos: string[];
  source: string | null;
  demand: number;
  open_reports: number;
  created_at: string;
  updated_at: string;
};

export type AdminWordDetail = {
  entry: WordEntry;
  form: WordEntryIn;
  versions: { version: number; reason: string | null; changed_by: string | null; created_at: string }[];
  reports: { id: number; reason: string; comment: string | null; status: string; created_at: string }[];
};
