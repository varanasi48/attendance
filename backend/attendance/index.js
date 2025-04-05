const axios = require('axios');
const { MongoClient } = require('mongodb');

module.exports = async function (context, req) {
    const { phone, image } = req.body;

    if (!phone || !image) {
        context.res = {
            status: 400,
            body: "Phone and image are required."
        };
        return;
    }

    try {
        const faceApiResponse = await axios.post(
            'https://attendance-face.cognitiveservices.azure.com/face/v1.0/detect',
            {
                url: image // For base64, you'd change this to data and content-type
            },
            {
                headers: {
                    'Ocp-Apim-Subscription-Key': process.env.FACE_API_KEY,
                    'Content-Type': 'application/json'
                }
            }
        );

        const faceDetected = faceApiResponse.data;

        const client = new MongoClient(process.env.MONGO_DB_CONNECTION_STRING);
        await client.connect();
        const db = client.db('attendanceDB');
        const collection = db.collection('attendance');

        await collection.insertOne({
            phone,
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
