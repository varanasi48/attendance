module.exports = async function (context, req) {
    context.log('Attendance function triggered.');

    try {
        const { phoneNumber, faceImage } = req.body;

        // Simple test return without doing anything
        context.res = {
            status: 200,
            body: {
                success: true,
                message: 'Function received data successfully!',
                phoneNumber,
                receivedImage: faceImage ? true : false
            }
        };
    } catch (error) {
        context.res = {
            status: 500,
            body: {
                success: false,
                message: 'Error in function.',
                error: error.message
            }
        };
    }
};
