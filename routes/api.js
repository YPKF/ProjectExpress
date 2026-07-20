const express = require('express');
const { allQuery } = require('../database');

const router = express.Router();

// -----------------------------------------------------------------------
// GET /api/stats  — JSON stats for the dashboard widgets (SCRUM-11)
// -----------------------------------------------------------------------
router.get('/api/stats', (req, res) => {
  try {
    const totalRows = allQuery('SELECT COUNT(*) AS count FROM items');
    const total = totalRows.length > 0 ? Number(totalRows[0].count) : 0;

    const recent = allQuery(
      'SELECT id, name, created_at FROM items ORDER BY created_at DESC LIMIT ?',
      [5]
    );

    res.json({ total, recent });
  } catch (err) {
    console.error('Stats error:', err.message);
    res.status(500).json({ error: 'Unable to load stats.' });
  }
});

module.exports = router;
