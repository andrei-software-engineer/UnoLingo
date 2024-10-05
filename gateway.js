const express = require('express');
const axios = require('axios');
const redis = require('redis');
const app = express();

const client = redis.createClient();  // Redis client for caching

app.get('/status', async (req, res) => {
    try {
        let serviceAStatus = await axios.get('http://localhost:5002/status');
        let serviceBStatus = await axios.get('http://localhost:5001/status');
        res.json({
            "Service A": serviceAStatus.data,
            "Service B": serviceBStatus.data
        });
    } catch (err) {
        res.status(500).json({ error: 'Error communicating with services' });
    }
});

app.get('/communicate', async (req, res) => {
    try {
        const cacheKey = 'service_a_message';
        client.get(cacheKey, async (err, data) => {
            if (data) {
                return res.json({ "message_from_cache": JSON.parse(data) });
            } else {
                let response = await axios.get('http://localhost:5002/communicate');
                client.setex(cacheKey, 60, JSON.stringify(response.data));  // Cache for 60 seconds
                res.json({ "message_from_service_a": response.data });
            }
        });
    } catch (err) {
        res.status(500).json({ error: 'Error communicating with Service A' });
    }
});

app.listen(3000, () => {
    console.log('Gateway is running on port 3000');
});
