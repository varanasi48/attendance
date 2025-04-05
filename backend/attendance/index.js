const axios = require('axios');
const { MongoClient } = require('mongodb');

module.exports = async function (context, req) {
    try {
        const { phoneNumber, faceImage } = req.body;
        
        console.log("Received request body:", req.body);
        console.log("Phone:", phoneNumber);
        console.log("Face image size:", faceImage ? faceImage.length : 'No image received');

        if (!phoneNumber || !faceImage) {
            context.res = {
                status: 400,
                body: "Phone number and face image are required."
            };
            return;
        }

        // Continue with Face API, etc...
    } catch (err) {
        console.error("Unexpected server error:", err);
        context.res = {
            status: 500,
            body: "Internal server error."
        };
    }
};

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
};.


console.log("BODY:", req.body);
console.log("Phone:", phoneNumber);
console.log("Face Image:", faceImage?.substring(0, 100));
