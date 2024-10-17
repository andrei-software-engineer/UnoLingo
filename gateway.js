const express = require('express');
const axios = require('axios');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Create a rate limiter for the /register route
const registerLimiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 10, // Limit each IP to 10 requests per windowMs
    message: { error: "Too many requests, please try again later." },
});

// Service Discovery URL
const SERVICE_DISCOVERY_URL = 'http://localhost:8080';

// Middleware for setting request timeout
const timeoutMiddleware = (req, res, next) => {
    res.setTimeout(2000, () => {
        console.error('Request has timed out.');
        res.status(504).json({ error: 'Request timed out. Please try again.' });
    });
    next();
};

// Use the timeout middleware for all routes
app.use(timeoutMiddleware);

// Proxy endpoints to the authentication service

// Function to discover a service
const discoverService = async (serviceName) => {
    try {
        const response = await axios.get(`${SERVICE_DISCOVERY_URL}/services/${serviceName}`);
        console.log(response.data);
        return response.data["serviceUrl"]; // Return the first available service URL
    } catch (error) {
        console.error('Service discovery failed:', error.message);
        throw new Error('Service discovery failed');
    }
};

// Register new user
app.post('/gateway/register', registerLimiter, async (req, res) => {
    try {
        const authServiceUrl = await discoverService('auth_service');
        const response = await axios.post(`${authServiceUrl}/register`, req.body);
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Login and issue JWT token
app.post('/gateway/login', async (req, res) => {
    try {
        const authServiceUrl = await discoverService('auth_service');
        const response = await axios.post(`${authServiceUrl}/login`, req.body);
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Validate JWT token
app.get('/gateway/validate_token', async (req, res) => {
    try {
        const authServiceUrl = await discoverService('auth_service');
        const response = await axios.get(`${authServiceUrl}/validate_token`, {
            headers: {
                'Authorization': req.headers['authorization'] // Forward the Authorization header
            }
        });
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Get user information by ID
app.get('/gateway/user/:id', async (req, res) => {
    try {
        const authServiceUrl = await discoverService('auth_service');
        const response = await axios.get(`${authServiceUrl}/user/${req.params.id}`);
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Get all users
app.get('/gateway/users', async (req, res) => {
    try {
        const authServiceUrl = await discoverService('auth_service');
        const response = await axios.get(`${authServiceUrl}/users`);
        res.status(response.status).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
    }
});

// Gateway status endpoint
app.get('/status', async (req, res) => {
    try {
        const authServiceUrl = await discoverService('auth_service');
        const authServiceResponse = await axios.get(`${authServiceUrl}/status`);

        res.status(200).json({
            gateway: {
                status: 'Gateway is running',
            },
            authenticationService: authServiceResponse.data,
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to retrieve service status.' });
    }
});

// test the task timeouts
app.get('/gateway/slow', async (req, res) => {
    try {
        const authServiceUrl = await discoverService('auth_service');
        const url = `${authServiceUrl}/slow_endpoint`;
        console.log('Requesting URL:', url);
        const response = await axios.get(url);
        res.status(response.status).json(response.data);
    } catch (error) {
        console.error('Error occurred:', error);
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Error' });
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Gateway running on http://localhost:${PORT}`);
});
