// Centralized error-handling middleware (SCRUM-8)
// Normalizes error responses and avoids leaking stack traces to clients.

function notFound(req, res, next) {
  res.status(404).render('index', {
    title: '404 — Page Not Found',
    message: 'The page you requested does not exist.',
  });
}

function errorHandler(err, req, res, _next) {
  const status = err.status || 500;
  // Log full detail server-side only.
  console.error(`[${status}] ${req.method} ${req.originalUrl}:`, err.stack);
  res.status(status).json({
    error: status === 500 ? 'An unexpected error occurred.' : err.message,
  });
}

module.exports = { notFound, errorHandler };
