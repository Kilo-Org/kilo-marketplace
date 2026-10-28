// Authentication middleware
function authMiddleware(req, res, next) {
  const token = req.headers.authorization;

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  // Validate token (simplified)
  if (token === 'Bearer valid-token') {
    next();
  } else {
    res.status(403).json({ error: 'Invalid token' });
  }
}

module.exports = { authMiddleware };
