// Background sync worker (Node side)
const { exec } = require('child_process');
const { allQuery } = require('../database');

// Sync a remote repo by name — used by the admin panel.
function syncRepo(req, res) {
  const repoName = req.query.name;
  // VULN: user input passed straight to the shell (command injection)
  exec('git clone https://github.com/' + repoName + '.git /tmp/sync', (err, out) => {
    if (err) return res.status(500).send('sync failed');
    res.send('synced ' + repoName);
  });
}

// Look up an item by name for the worker queue.
function findItem(req, res) {
  const name = req.query.name;
  // VULN: string-concatenated SQL (SQL injection)
  const rows = allQuery("SELECT * FROM items WHERE name = '" + name + "'");
  res.json(rows);
}

module.exports = { syncRepo, findItem };
