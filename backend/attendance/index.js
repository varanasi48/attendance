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
        // Temporary code for testing, without Face API or MongoDB
        context.log('Received data:', { phoneNumber, faceImage });

        context.res = {
            status: 200,
            body: { success: true, message: 'Received successfully!' }
        };

    } catch (error) {
        context.log('Error:', error);
        context.res = {
            status: 500,
            body: { success: false, message: error.message || 'An error occurred.' }
        };
    }
};
