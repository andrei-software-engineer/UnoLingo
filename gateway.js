// server.js

const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
const PORT = 3000; // You can change this to any available port

// Middleware
app.use(cors());
app.use(express.json()); // Parse JSON bodies

// Authentication microservice URL
const AUTH_SERVICE_URL = 'http://localhost:5003';

// Proxy endpoints to the authentication service

// Register new user
app.post('/gateway/register', async (req, res) => {
    try {
        const response = await axios.post(`${AUTH_SERVICE_URL}/register`, req.body);
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Login and issue JWT token
app.post('/login', async (req, res) => {
    try {
        const response = await axios.post(`${AUTH_SERVICE_URL}/login`, req.body);
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Validate JWT token
app.get('/gateway/validate_token', async (req, res) => {
    try {
        const response = await axios.get(`${AUTH_SERVICE_URL}/validate_token`, {
            headers: {
                'Authorization': req.headers['authorization'] // Forward the Authorization header
            }
        });
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Gateway running on http://localhost:${PORT}`);
});
