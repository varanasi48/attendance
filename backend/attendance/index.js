const axios = require('axios');
const { MongoClient } = require('mongodb');

module.exports = async function (context, req) {
    const { phoneNumber, faceImage } = req.body;

    // Log the request body to understand what we're receiving
    context.log('Received body:', req.body);

    if (!phoneNumber || !faceImage) {
        context.res = {
            status: 400,
            body: "Phone number and face image are required."
        };
        context.log('Error: Missing phone number or face image');
        return;
    }

    try {
        // Log before calling the Face API
        context.log('Calling Face API with phoneNumber:', phoneNumber);

        // Call the Face API (ensure the correct endpoint and parameters)
        const faceApiResponse = await axios.post(
            'https://attendance-face.cognitiveservices.azure.com/face/v1.0/detect',
            Buffer.from(faceImage.split(',')[1], 'base64'),
            {
                headers: {
                    'Ocp-Apim-Subscription-Key': process.env.FACE_API_KEY,
                    'Content-Type': 'application/octet-stream'
                },
                params: {
                    returnFaceId: true
                }
            }
        );

        // Log the response from the Face API
        context.log('Face API Response:', faceApiResponse.data);

        // Save to MongoDB
        const client = new MongoClient(process.env.MONGO_DB_CONNECTION_STRING);
        await client.connect();
        const db = client.db('attendanceDB');
        const collection = db.collection('attendance');

        context.log('Inserting attendance data for phone:', phoneNumber);

        await collection.insertOne({
            phoneNumber,
            faceDetected: faceApiResponse.data,
            timestamp: new Date()
        });

        context.res = {
            status: 200,
            body: { success: true, message: 'Attendance marked successfully!' }
        };
    } catch (error) {
        // Log the error to see what caused the failure
        context.log.error('Error in function execution:', error);

        context.res = {
            status: 500,
            body: { success: false, message: error.message }
        };
    }
};
