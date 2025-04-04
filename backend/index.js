const axios = require('axios');
const { MongoClient } = require('mongodb');

module.exports = async function (context, req) {
    const { phoneNumber, faceImageBase64 } = req.body;

    if (!phoneNumber || !faceImageBase64) {
        context.res = {
            status: 400,
            body: "Phone number and face image (Base64) are required."
        };
        return;
    }

    try {
        // Convert base64 image to buffer
        const imageBuffer = Buffer.from(faceImageBase64, 'base64');

        // Call Azure Face API
        const faceApiResponse = await axios.post(
            `${process.env.FACE_API_ENDPOINT}/face/v1.0/detect?returnFaceId=true`,
            imageBuffer,
            {
                headers: {
                    'Content-Type': 'application/octet-stream',
                    'Ocp-Apim-Subscription-Key': process.env.FACE_API_KEY
                }
            }
        );

        if (!faceApiResponse.data.length) {
            context.res = {
                status: 400,
                body: "No face detected in the image."
            };
            return;
        }

        const faceId = faceApiResponse.data[0].faceId;

        // Connect to MongoDB and save attendance
        const client = new MongoClient(process.env.MONGO_DB_CONNECTION_STRING);
        await client.connect();
        const db = client.db('attendanceDB');
        const collection = db.collection('attendance');

        await collection.insertOne({
            phoneNumber,
            faceId,
            timestamp: new Date()
        });

        context.res = {
            status: 200,
            body: { success: true, message: 'Attendance marked successfully.' }
        };

    } catch (error) {
        console.error("Error:", error.message);
        context.res = {
            status: 500,
            body: { success: false, message: error.message }
        };
    }
};
