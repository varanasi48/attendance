const axios = require('axios');
const { MongoClient } = require('mongodb');

module.exports = async function (context, req) {
    context.log('Function started');
    context.log('Request body:', req.body);

    const { phoneNumber, faceImage } = req.body;

    if (!phoneNumber || !faceImage) {
        context.res = {
            status: 400,
            body: "Phone number and face image are required."
        };
        context.log('Invalid input: Missing phone number or face image');
        return;
    }

    try {
        context.log('Calling Face API...');
        const faceApiResponse = await axios.post('https://attendance-face.cognitiveservices.azure.com/face/v1.0/detect', {
            image: faceImage,
            apiKey: process.env.FACE_API_KEY
        });
        
        context.log('Face API Response:', faceApiResponse.data);

        // Simulate MongoDB insertion logic (replace with actual DB code)
        const dbResult = await simulateDatabaseInsert();
        context.log('Database result:', dbResult);

        context.res = {
            status: 200,
            body: { success: true, message: 'Attendance marked successfully!' }
        };
    } catch (error) {
        context.error('Error during function execution:', error.message, error.stack);
        context.res = {
            status: 500,
            body: { success: false, message: 'An error occurred during execution.', error: error.message }
        };
    }
};
