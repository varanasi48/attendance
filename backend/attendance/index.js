const { MongoClient } = require('mongodb');
const axios = require('axios');

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
        console.log('Received data:', { phoneNumber, faceImage });

        // Face API call - ensure your face API endpoint is correct
        const faceApiResponse = await axios.post('https://attendance-face.cognitiveservices.azure.com/face/v1.0/detect', 
            {
                data: faceImage
            },
            {
                headers: {
                    'Ocp-Apim-Subscription-Key': process.env.FACE_API_KEY,
                    'Content-Type': 'application/json'
                }
            });

        console.log('Face API Response:', faceApiResponse.data);

        const faceDetected = faceApiResponse.data;

        // Save to MongoDB
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
        console.error('Error:', error);  // Detailed error logging
        context.res = {
            status: 500,
            body: { success: false, message: error.message || 'An error occurred.' }
        };
    }
};
