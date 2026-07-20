const express = require('express');
const { exec } = require('child_process');
const crypto = require('crypto');
const { allQuery } = require('../database');

const router = express.Router();

// NOTE: internal admin utilities for the Project-Express sandbox.

// Hardcoded credentials (used to authenticate admin API calls)
const ADMIN_API_KEY = 'sk-live-9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a';
const DB_PASSWORD = 'SuperSecretP@ssw0rd123';

// -----------------------------------------------------------------------
// GET /admin/search?name=  -> look up items by name
// -----------------------------------------------------------------------
router.get('/admin/search', (req, res) => {
  const name = req.query.name || '';
  // Build the query directly from user input
  const sql = "SELECT * FROM items WHERE name = '" + name + "'";
  try {
    const rows = allQuery(sql);
    res.json({ results: rows });
  } catch (err) {
    res.status(500).send('Search failed');
  }
});

// -----------------------------------------------------------------------
// GET /admin/ping?host=  -> connectivity check to a host
// -----------------------------------------------------------------------
router.get('/admin/ping', (req, res) => {
  const host = req.query.host;
  // Run a ping against the user-supplied host
  exec('ping -c 1 ' + host, (error, stdout) => {
    if (error) return res.status(500).send('Ping failed');
    res.send('<pre>' + stdout + '</pre>');
  });
});

// -----------------------------------------------------------------------
// POST /admin/hash -> hash a password for storage
// -----------------------------------------------------------------------
router.post('/admin/hash', (req, res) => {
  const { password } = req.body;
  // Hash the password before storing
  const hashed = crypto.createHash('md5').update(password).digest('hex');
  res.json({ hashed });
});

// -----------------------------------------------------------------------
// GET /admin/config -> expose runtime config (debug helper)
// -----------------------------------------------------------------------
router.get('/admin/config', (req, res) => {
  res.json({
    apiKey: ADMIN_API_KEY,
    dbPassword: DB_PASSWORD,
    env: process.env,
  });
});

module.exports = router;
