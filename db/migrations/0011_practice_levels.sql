-- Judge-local manual overrides. An absent judge means use profile heuristics.
-- CSES stays in cses_band for compatibility with existing saved choices.
ALTER TABLE user_preferences
  ADD COLUMN IF NOT EXISTS practice_levels JSONB NOT NULL DEFAULT '{}'::jsonb
  CHECK (jsonb_typeof(practice_levels) = 'object');
