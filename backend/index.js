const { FunctionApp } = require('@azure/functions');
const axios = require('axios');
const { MongoClient } = require('mongodb');

// Example of an HTTP trigger function to mark attendance
module.exports = async function (context, req) {
    const { phoneNumber, faceImage } = req.body;

    if (!phoneNumber || !faceImage) {
        context.res = {
            status: 400,
            body: "Phone number and face image are required."
        };
        return;
    }

    try {
        // Call Face API to detect face (replace with actual logic)
        const faceApiResponse = await axios.post('https://attendance-face.cognitiveservices.azure.com/ {
            image: faceImage,
            apiKey: process.env.FACE_API_KEY
        });

        // Process face API response (e.g., verify face, extract data)
        const faceDetected = faceApiResponse.data;

        // Save attendance to MongoDB (or other DB)
        const client = new MongoClient(process.env.MONGO_DB_CONNECTION_STRING);
        await client.connect();
        const db = client.db('attendanceDB');
        const collection = db.collection('attendance');
        
        await collection.insertOne({
            phoneNumber,
            faceDetected,
            timestamp: new Date()
        });

        context.res = {
            status: 200,
            body: { success: true, message: 'Attendance marked successfully!' }
        };
    } catch (error) {
        context.res = {
            status: 500,
            body: { success: false, message: error.message }
        };
    }
};
