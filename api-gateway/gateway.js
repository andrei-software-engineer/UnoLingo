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
const SERVICE_DISCOVERY_URL = 'http://service-discovery:8080';

// Middleware for setting request timeout
const timeoutMiddleware = (req, res, next) => {
    res.setTimeout(9000, () => {
        console.error('Request has timed out.');
        res.status(504).json({ error: 'Request timed out. Please try again.' });
    });
    next();
};

// Use the timeout middleware for all routes
app.use(timeoutMiddleware);

// Proxy endpoints to the authentication service

// Function to discover a service, fetch the url of the specified service from the discovery endpoint
const discoverService = async (serviceName) => {
    try {
        // console.log(serviceName);
        const response = await axios.get(`http://service-discovery:8080/services/${serviceName}`);
        // console.log(response.data["serviceUrl"]);
        return response.data["serviceUrl"]; // Return the first available service URL
    } catch (error) {
        console.error('Service discovery failed:', error.message);
        throw new Error('Service discovery failed');
    }
};

const failedServices = new Map(); // Track failing services and their retry times

// Helper to check if a service is temporarily unavailable
const isServiceBlocked = (serviceUrl) => {
    const blockedUntil = failedServices.get(serviceUrl);
    return blockedUntil && Date.now() < blockedUntil;
};

// Helper to block a service temporarily
const blockService = (serviceUrl) => {
    const blockDuration = 5 * 60 * 1000; // Block the service for 5 minutes
    failedServices.set(serviceUrl, Date.now() + blockDuration);
    console.log(`Service ${serviceUrl} blocked until ${new Date(Date.now() + blockDuration).toISOString()}`);
};

// Common retry logic function
const performRequestWithRetry = async (req, res, method, endpoint, body, headers = {}) => {
    const maxRetries = 3;
    const maxServiceSwitches = 2;
    let retryCount = 0;
    let serviceSwitchCount = 0;
    let currentServiceUrl;

    try {
        currentServiceUrl = await discoverService('auth_service');
    } catch (error) {
        return res.status(500).json({ error: 'Initial service discovery failed. Please try again later.' });
    }

    while (serviceSwitchCount < maxServiceSwitches) {
        if (isServiceBlocked(currentServiceUrl)) {
            console.log(`Skipping blocked service: ${currentServiceUrl}`);
            try {
                currentServiceUrl = await discoverService('auth_service');
                serviceSwitchCount++;
                continue;
            } catch (error) {
                return res.status(500).json({ error: 'Service discovery failed. Please try again later.' });
            }
        }

        while (retryCount < maxRetries) {
            try {
                console.log(`Attempting ${method} at ${currentServiceUrl}${endpoint}, retry ${retryCount + 1}`);
                const response = await axios({
                    method,
                    url: `${currentServiceUrl}${endpoint}`,
                    data: body,
                    headers
                });
                return res.status(response.status).json(response.data); // Success
            } catch (error) {
                retryCount++;
                console.error(`${method} attempt ${retryCount} failed at ${currentServiceUrl}:`, error.message);

                if (retryCount === maxRetries) {
                    blockService(currentServiceUrl);
                }

                if (!error.response || error.response?.status >= 500) continue; // Retry only for 500+ errors or no response
                return res.status(error.response?.status || 500).json(error.response?.data || { error: 'Internal Server Error' });
            }
        }

        retryCount = 0;
        serviceSwitchCount++;
        try {
            currentServiceUrl = await discoverService('auth_service');
        } catch (error) {
            return res.status(500).json({ error: 'Service discovery failed. Please try again later.' });
        }
    }

    return res.status(500).json({ error: `Failed to process ${method} request after multiple attempts.` });
};

// Routes

// Register new user
app.post('/gateway/register', registerLimiter, (req, res) => {
    performRequestWithRetry(req, res, 'POST', '/register', req.body);
});

// Login and issue JWT token
app.post('/gateway/login', (req, res) => {
    performRequestWithRetry(req, res, 'POST', '/login', req.body);
});

// Validate JWT token
app.get('/gateway/validate_token', (req, res) => {
    performRequestWithRetry(req, res, 'GET', '/validate_token', null, {
        Authorization: req.headers['authorization']
    });
});

// Get user information by ID
app.get('/gateway/user/:id', (req, res) => {
    performRequestWithRetry(req, res, 'GET', `/user/${req.params.id}`);
});

// Get all users
app.get('/gateway/users', (req, res) => {
    performRequestWithRetry(req, res, 'GET', '/users');
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


// Start the server
app.listen(PORT, () => {
    console.log(`Gateway running on http://localhost:${PORT}`);
});