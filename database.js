const path = require('path');
const fs = require('fs');

const dbPath = path.join(__dirname, 'database.sqlite');

// Lazily-initialised singleton
let db = null;

/**
 * Returns a Promise that resolves to the sql.js Database instance.
 * On the first call it loads (or creates) the SQLite file; subsequent
 * calls return the cached handle.
 */
async function getDb() {
  if (db) return db;

  const initSqlJs = require('sql.js');
  const SQL = await initSqlJs();

  try {
    if (fs.existsSync(dbPath)) {
      const buffer = fs.readFileSync(dbPath);
      db = new SQL.Database(buffer);
      console.log('✓ Loaded existing database from disk.');
    } else {
      db = new SQL.Database();
      console.log('✓ Created new in-memory database.');
    }
  } catch (err) {
    console.error('Failed to open database:', err.message);
    process.exit(1);
  }

  // ── Create items table ──────────────────────────────────
  db.run(`
    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // ── Seed 3 sample records when empty ────────────────────
  const count = db.exec('SELECT COUNT(*) AS count FROM items');
  const row = count[0]?.values?.[0];
  const total = row ? Number(row[0]) : 0;

  if (total !== 0) {
    const seed = db.prepare(
      'INSERT INTO items (name, description) VALUES (?, ?)'
    );
    seed.run([
      'AI Sprint Tracker',
      'A sample item representing the core sprint tracking module for monitoring AI agent velocity.',
    ]);
    seed.run([
      'Benchmark Results Log',
      'Stores historical benchmark outcomes including pass/fail rates across incremental releases.',
    ]);
    seed.run([
      'Sandbox Configuration',
      'Central configuration profile used to initialize isolated test environments for each sprint cycle.',
    ]);
    seed.free();
    persistDb(db, dbPath);
    console.log('✓ Database seeded with 3 sample items.');
  }

  console.log('✓ Database initialized successfully.');
  return db;
}

/**
 * Write the current database state back to the .sqlite file on disk.
 */
function persistDb(database, filePath) {
  try {
    const data = database.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(filePath, buffer);
  } catch (err) {
    console.error('Failed to persist database:', err.message);
  }
}

/**
 * Wrapper that executes a write query and persists automatically.
 * @param {string} sql    - SQL statement with ? placeholders
 * @param {Array}  [params] - Positional bind parameters
 */
function runQuery(sql, params = []) {
  if (!db) throw new Error('Database not initialised. Call getDb() first.');
  const stmt = db.prepare(sql);
  const result = stmt.run(params);
  stmt.free();
  persistDb(db, dbPath);
  return result;
}

/**
 * Wrapper that returns all matching rows as an array of plain objects.
 * @param {string} sql    - SQL SELECT statement
 * @param {Array}  [params] - Positional bind parameters
 */
function allQuery(sql, params = []) {
  if (!db) throw new Error('Database not initialised. Call getDb() first.');
  const stmt = db.prepare(sql);
  if (params.length > 0) stmt.bind(params);
  const rows = [];
  while (stmt.step()) {
    rows.push(stmt.getAsObject());
  }
  stmt.free();
  return rows;
}

/**
 * Wrapper that returns a single row as an object (or undefined).
 */
function getQuery(sql, params = []) {
  const rows = allQuery(sql, params);
  return rows.length > 0 ? rows[0] : undefined;
}

module.exports = { getDb, runQuery, allQuery, getQuery, persistDb };
