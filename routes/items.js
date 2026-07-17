const express = require('express');
const { allQuery, runQuery } = require('../database');

const router = express.Router();

// -----------------------------------------------------------------------
// GET  /  – Home page
// -----------------------------------------------------------------------
router.get('/', (req, res) => {
  res.render('index', {
    title: 'Home — Project-Express',
    message: null,
  });
});

// -----------------------------------------------------------------------
// GET  /dashboard  – Dashboard (high-level summary)
// -----------------------------------------------------------------------
router.get('/dashboard', (req, res) => {
  try {
    const rows = allQuery('SELECT COUNT(*) AS count FROM items');
    const totalItems = rows.length > 0 ? Number(rows[0].count) : 0;

    const recentItems = allQuery(
      'SELECT * FROM items ORDER BY created_at DESC LIMIT 5'
    );
    const newestItem = recentItems.length > 0 ? recentItems[0] : null;

    res.render('dashboard', {
      title: 'Dashboard — Project-Express',
      totalItems,
      recentItems,
      newestItem,
    });
  } catch (err) {
    console.error('Dashboard error:', err.message);
    res.status(500).send('Unable to load dashboard. Please try again.');
  }
});

// -----------------------------------------------------------------------
// GET  /items  – List all items
// -----------------------------------------------------------------------
router.get('/items', (req, res) => {
  try {
    const items = allQuery('SELECT * FROM items ORDER BY created_at DESC');

    res.render('items', { title: 'Manage Items', items });
  } catch (err) {
    console.error('Items error:', err.message);
    res.status(500).send('Unable to load items. Please try again.');
  }
});

// -----------------------------------------------------------------------
// POST /items  – Create a new item
// -----------------------------------------------------------------------
router.post('/items', (req, res) => {
  try {
    const { name, description } = req.body;

    if (!name || !name.trim()) {
      return res
        .status(400)
        .send('Item name is required and cannot be empty.');
    }

    runQuery('INSERT INTO items (name, description) VALUES (?, ?)', [
      name.trim(),
      (description || '').trim(),
    ]);

    res.redirect('/items');
  } catch (err) {
    console.error('Create item error:', err.message);
    res.status(500).send('Failed to create item.');
  }
});

// -----------------------------------------------------------------------
// POST /items/:id/update  – Update an existing item
// -----------------------------------------------------------------------
router.post('/items/:id/update', (req, res) => {
  try {
    const { id } = req.params;
    const { name, description } = req.body;

    if (!name || !name.trim()) {
      return res
        .status(400)
        .send('Item name is required and cannot be empty.');
    }

    runQuery('UPDATE items SET name = ?, description = ? WHERE id = ?', [
      name.trim(),
      (description || '').trim(),
      id,
    ]);

    res.redirect('/items');
  } catch (err) {
    console.error('Update item error:', err.message);
    res.status(500).send('Failed to update item.');
  }
});

// -----------------------------------------------------------------------
// POST /items/:id/delete  – Delete an item
// -----------------------------------------------------------------------
router.post('/items/:id/delete', (req, res) => {
  try {
    const { id } = req.params;

    runQuery('DELETE FROM items WHERE id = ?', [id]);

    res.redirect('/items');
  } catch (err) {
    console.error('Delete item error:', err.message);
    res.status(500).send('Failed to delete item.');
  }
});

module.exports = router;
