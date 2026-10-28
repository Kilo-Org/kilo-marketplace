const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

// Just a regular REST API gateway - no Kafka here
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.post('/api/orders', async (req, res) => {
  // Calls downstream services via HTTP
  const result = await axios.post('http://order-service/orders', req.body);
  res.json(result.data);
});

app.get('/api/users/:id', async (req, res) => {
  const user = await axios.get(`http://user-service/users/${req.params.id}`);
  res.json(user.data);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});
