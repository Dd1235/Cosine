-- A study preference, like cses_band. NULL = never chose, distinct from an
-- explicit false, so the default can move later without rewriting choices.
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS show_labels BOOLEAN;
