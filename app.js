const express = require('express');
const path = require('path');
const { getDb } = require('./database');
const itemsRouter = require('./routes/items');

// ---------------------------------------------------------------------------
// Bootstrap – initialise database then start listening
// ---------------------------------------------------------------------------
async function bootstrap() {
  const db = await getDb();

  const app = express();
  const PORT = process.env.PORT || 3000;

  // Middleware
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  app.use(express.static(path.join(__dirname, 'public')));

  // View engine
  app.set('view engine', 'ejs');
  app.set('views', path.join(__dirname, 'views'));

  // Attach database helpers to every request
  app.use((req, _res, next) => {
    req.db = db;
    next();
  });

  // Routes
  app.use('/', itemsRouter);

  // 404 handler
  app.use((req, res) => {
    res.status(404).render('index', {
      title: '404 — Page Not Found',
      message:
        'The page you requested does not exist. Use the navigation above to return.',
    });
  });

  // Global error handler
  app.use((err, _req, res, _next) => {
    console.error('Unhandled error:', err.stack);
    res.status(500).send('An unexpected error occurred. Please try again later.');
  });

  app.listen(PORT, () => {
    console.log(`\n  🚀  Project-Express`);
    console.log(`  ─────────────────────────────────`);
    console.log(`  ➜  Local:   http://localhost:${PORT}`);
    console.log(`  ➜  Home:    http://localhost:${PORT}/`);
    console.log(`  ➜  Dashboard: http://localhost:${PORT}/dashboard`);
    console.log(`  ➜  Items:   http://localhost:${PORT}/items\n`);
  });
}

bootstrap().catch((err) => {
  console.error('Failed to start server:', err.message);
  process.exit(1);
});
