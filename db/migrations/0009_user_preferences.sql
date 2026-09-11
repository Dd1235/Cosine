-- Explicit judge-local starting band; no conversion from external ratings.
CREATE TABLE IF NOT EXISTS user_preferences (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  cses_band SMALLINT CHECK (cses_band BETWEEN 1 AND 5),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
