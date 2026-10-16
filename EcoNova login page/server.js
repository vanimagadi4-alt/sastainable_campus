// EcoNova auth server: Express + SQLite + bcrypt + JWT (httpOnly cookie)
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const express = require('express');
const helmet = require('helmet');
const cookieParser = require('cookie-parser');
const rateLimit = require('express-rate-limit');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const Database = require('better-sqlite3');

const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET;
const IS_PROD = process.env.NODE_ENV === 'production';
if (!JWT_SECRET || JWT_SECRET.length < 32) {
  console.error('Set JWT_SECRET (32+ characters) in .env. See .env.example.');
  process.exit(1);
}

/* ---------- Database ---------- */
const db = new Database(path.join(__dirname, 'econova.db'));
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
db.exec(fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8'));

const q = {
  byEmail:   db.prepare('SELECT * FROM users WHERE email = ?'),
  byId:      db.prepare('SELECT id, username, email, role, created_at FROM users WHERE id = ?'),
  insert:    db.prepare('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)'),
  touch:     db.prepare("UPDATE users SET last_login_at = datetime('now') WHERE id = ?"),
  setPass:   db.prepare('UPDATE users SET password_hash = ? WHERE id = ?'),
  allUsers:  db.prepare('SELECT id, username, email, role, created_at, last_login_at FROM users ORDER BY id'),
  addReset:  db.prepare('INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)'),
  getReset:  db.prepare("SELECT * FROM password_resets WHERE token_hash = ? AND used = 0 AND expires_at > datetime('now')"),
  useReset:  db.prepare('UPDATE password_resets SET used = 1 WHERE id = ?')
};

// Optional: seed an admin (admins can't be created through public sign-up)
if (process.env.ADMIN_EMAIL && process.env.ADMIN_PASSWORD && !q.byEmail.get(process.env.ADMIN_EMAIL)) {
  q.insert.run(process.env.ADMIN_USERNAME || 'admin', process.env.ADMIN_EMAIL,
               bcrypt.hashSync(process.env.ADMIN_PASSWORD, 12), 'admin');
  console.log('Seeded admin account:', process.env.ADMIN_EMAIL);
}

/* ---------- Helpers ---------- */
const emailRx = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const DUMMY_HASH = bcrypt.hashSync('timing-equalizer', 12); // makes unknown-email logins take the same time
const sha256 = v => crypto.createHash('sha256').update(v).digest('hex');
const publicUser = u => ({ id: u.id, username: u.username, email: u.email, role: u.role });

function setSession(res, user, remember) {
  const ttl = remember ? 30 * 24 * 3600 : 8 * 3600; // seconds
  const token = jwt.sign({ sub: user.id, role: user.role }, JWT_SECRET, { expiresIn: ttl });
  res.cookie('session', token, {
    httpOnly: true, sameSite: 'strict', secure: IS_PROD,
    ...(remember ? { maxAge: ttl * 1000 } : {}) // no maxAge = session cookie
  });
}

function requireAuth(req, res, next) {
  try {
    const { sub } = jwt.verify(req.cookies.session, JWT_SECRET);
    const user = q.byId.get(sub);
    if (!user) throw new Error('gone');
    req.user = user;
    next();
  } catch {
    res.status(401).json({ error: 'Please log in.' });
  }
}
const requireRole = role => (req, res, next) =>
  req.user.role === role ? next() : res.status(403).json({ error: 'Not allowed.' });

/* ---------- App ---------- */
const app = express();
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],   // the page uses inline <script>/<style>
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:'],
      upgradeInsecureRequests: null               // allow plain http on localhost
    }
  }
}));
app.use(express.json({ limit: '10kb' }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, limit: 30, standardHeaders: true, legacyHeaders: false,
  message: { error: 'Too many attempts. Try again in a few minutes.' }
});
app.use('/api/signup', authLimiter);
app.use('/api/login', authLimiter);
app.use('/api/forgot-password', authLimiter);
app.use('/api/reset-password', authLimiter);

/* ----- Sign up: always creates a STUDENT; the role button is ignored here ----- */
app.post('/api/signup', async (req, res) => {
  const { username = '', email = '', password = '' } = req.body || {};
  if (String(username).trim().length < 3) return res.status(400).json({ error: 'Username must be at least 3 characters.' });
  if (!emailRx.test(String(email).trim())) return res.status(400).json({ error: 'Enter a valid email address.' });
  if (String(password).length < 8) return res.status(400).json({ error: 'Password must be at least 8 characters.' });

  try {
    const hash = await bcrypt.hash(String(password), 12);
    const info = q.insert.run(String(username).trim(), String(email).trim(), hash, 'student');
    res.status(201).json({ user: publicUser(q.byId.get(info.lastInsertRowid)) });
  } catch (err) {
    if (String(err.code).startsWith('SQLITE_CONSTRAINT')) {
      return res.status(409).json({ error: 'That username or email is already registered.' });
    }
    console.error(err);
    res.status(500).json({ error: 'Server error.' });
  }
});

/* ----- Login: the selected role must match the account's stored role ----- */
app.post('/api/login', async (req, res) => {
  const { email = '', password = '', role = 'Student', remember = false } = req.body || {};
  const user = q.byEmail.get(String(email).trim());
  const ok = await bcrypt.compare(String(password), user ? user.password_hash : DUMMY_HASH);
  if (!user || !ok) return res.status(401).json({ error: 'Incorrect email or password.' });
  if (user.role !== String(role).toLowerCase()) {
    return res.status(403).json({ error: `This account is not registered as ${role}.` });
  }
  q.touch.run(user.id);
  setSession(res, user, !!remember);
  res.json({ user: publicUser(user) });
});

app.post('/api/logout', (req, res) => { res.clearCookie('session'); res.json({ ok: true }); });
app.get('/api/me', requireAuth, (req, res) => res.json({ user: req.user }));

/* ----- Forgot / reset password ----- */
app.post('/api/forgot-password', (req, res) => {
  const user = q.byEmail.get(String(req.body?.email || '').trim());
  if (user) {
    const token = crypto.randomBytes(32).toString('hex');
    const expires = new Date(Date.now() + 15 * 60 * 1000).toISOString().slice(0, 19).replace('T', ' ');
    q.addReset.run(user.id, sha256(token), expires);
    // TODO: email this link (Nodemailer, SendGrid, etc.). Logged here for development only.
    console.log(`Password reset link for ${user.email}: http://localhost:${PORT}/reset.html?token=${token}`);
  }
  res.json({ ok: true }); // same reply whether or not the email exists
});

app.post('/api/reset-password', async (req, res) => {
  const { token = '', password = '' } = req.body || {};
  if (String(password).length < 8) return res.status(400).json({ error: 'Password must be at least 8 characters.' });
  const row = q.getReset.get(sha256(String(token)));
  if (!row) return res.status(400).json({ error: 'This reset link is invalid or has expired.' });
  const hash = await bcrypt.hash(String(password), 12);
  db.transaction(() => { q.setPass.run(hash, row.user_id); q.useReset.run(row.id); })();
  res.json({ ok: true });
});

/* ----- Example admin-only route ----- */
app.get('/api/admin/users', requireAuth, requireRole('admin'), (req, res) => {
  res.json({ users: q.allUsers.all() });
});

app.listen(PORT, () => console.log(`EcoNova auth running at http://localhost:${PORT}`));