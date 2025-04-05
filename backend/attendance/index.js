const axios = require('axios');
const { MongoClient } = require('mongodb');

module.exports = async function (context, req) {
    try {
        const { phoneNumber, faceImage } = req.body;
        
        console.log("Received request body:", req.body);

        if (!phoneNumber || !faceImage) {
            context.res = {
                status: 400,
                body: "Phone number and face image are required."
            };
            return;
        }

        // Call the Azure Face API
        const faceApiResponse = await axios.post(
            'https://attendance-face.cognitiveservices.azure.com/face/v1.0/detect',
            Buffer.from(faceImage.split(',')[1], 'base64'), // Convert base64 to binary
            {
                headers: {
                    'Ocp-Apim-Subscription-Key': process.env.FACE_API_KEY, // Azure Face API subscription key
                    'Content-Type': 'application/octet-stream' // Proper content type for binary data
                },
                params: {
                    returnFaceId: true // Ensure Face API returns face ID information
                }
            }
        );

        // Log Face API Response
        console.log("Face API response:", faceApiResponse.data);

        // Save attendance info to MongoDB
        const client = new MongoClient(process.env.MONGO_DB_CONNECTION_STRING);
        await client.connect();
        const db = client.db('attendanceDB');
        const collection = db.collection('attendance');
        
        await collection.insertOne({
            phoneNumber,
            faceDetected: faceApiResponse.data, // Store the face detection result
            timestamp: new Date()
        });

        context.res = {
            status: 200,
            body: { success: true, message: 'Attendance marked successfully!' }
        };

    } catch (error) {
        // Log the error
        console.error("Unexpected server error:", error);

        context.res = {
            status: 500,
            body: { success: false, message: error.message }
        };
    }
};
