const express = require('express');
const cors = require('cors');
const { createClient } = require('redis');  // New Redis client

// Create Redis client
const redisClient = createClient({
    url: 'redis://localhost:6379'
});

redisClient.on('connect', () => {
    console.log('Connected to Redis');
});

redisClient.on('error', (err) => {
    console.error('Redis error:', err);
});

redisClient.connect(); // Required in the new Redis client

const app = express();
const PORT = 8080;

app.use(cors());
app.use(express.json());

// Register a service and store it in Redis
app.post('/register', async (req, res) => {
    const { serviceName, serviceUrl } = req.body;

    if (!serviceName || !serviceUrl) {
        return res.status(400).json({ error: 'Service name and URL are required.' });
    }

    try {
        const services = await redisClient.lRange(serviceName, 0, -1); // Use lRange with async/await

        // Check if the service is already registered
        if (!services.includes(serviceUrl)) {
            await redisClient.rPush(serviceName, serviceUrl);  // Use rPush with async/await
            console.log(`Service registered: ${serviceName} - ${serviceUrl}`);
            return res.status(200).json({ message: 'Service registered successfully.' });
        } else {
            return res.status(200).json({ message: 'Service already registered.' });
        }
    } catch (err) {
        return res.status(500).json({ error: 'Error accessing Redis', details: err.message });
    }
});

// Deregister a service and remove it from Redis
app.post('/deregister', async (req, res) => {
    const { serviceName, serviceUrl } = req.body;

    try {
        const removedCount = await redisClient.lRem(serviceName, 0, serviceUrl);  // Use lRem with async/await

        if (removedCount > 0) {
            console.log(`Service deregistered: ${serviceName} - ${serviceUrl}`);
            return res.status(200).json({ message: 'Service deregistered successfully.' });
        } else {
            return res.status(404).json({ message: 'Service not found.' });
        }
    } catch (err) {
        return res.status(500).json({ error: 'Error deregistering service from Redis', details: err.message });
    }
});

// Discover services and rotate the first URL to the end using Redis
app.get('/services/:name', async (req, res) => {
    const serviceName = req.params.name;

    try {
        const services = await redisClient.lRange(serviceName, 0, -1);  // Use lRange with async/await

        if (services.length > 0) {
            // Rotate the service URLs: remove the first and push it to the end
            const serviceUrl = services[0];
            await redisClient.rPopLPush(serviceName, serviceName);  // Use rPopLPush with async/await

            return res.status(200).json({ serviceUrl: serviceUrl });
        } else {
            return res.status(404).json({ error: 'Service not found.' });
        }
    } catch (err) {
        return res.status(500).json({ error: 'Error accessing Redis', details: err.message });
    }
});

// Start the service discovery server
app.listen(PORT, () => {
    console.log(`Service Discovery running on http://localhost:${PORT}`);
});
