-- EcoNova auth schema (SQLite). Runs automatically on server start.

CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
  email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT    NOT NULL,                       -- bcrypt hash, never the raw password
  role          TEXT    NOT NULL DEFAULT 'student' CHECK (role IN ('admin', 'student')),
  created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
  last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS password_resets (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash  TEXT    NOT NULL UNIQUE,                  -- SHA-256 of the emailed token
  expires_at  TEXT    NOT NULL,
  used        INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_resets_user ON password_resets(user_id);