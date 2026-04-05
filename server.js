const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 8000;

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', service: 'bayqadam-frontend', port: PORT });
});

// Serve static files
app.use(express.static(__dirname));

// Handle HTML routes
app.get('*.html', (req, res) => {
  res.sendFile(path.join(__dirname, req.path));
});

// Fallback to index.html
app.get('*', (req, res) => {
  if (!path.extname(req.path)) {
    res.sendFile(path.join(__dirname, 'index.html'));
  } else {
    res.status(404).send('Not found');
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ BayQadam server running on http://0.0.0.0:${PORT}`);
});