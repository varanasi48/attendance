module.exports = async function (context, req) {
    // Log the incoming request for debugging purposes
    context.log('Received request:', req.body);

    // Check if we are getting data from the request
    if (!req.body || !req.body.phoneNumber || !req.body.faceImage) {
        context.res = {
            status: 400,
            body: "Phone number and face image are required."
        };
        return;
    }

    // Log the values we received
    context.log('Phone Number:', req.body.phoneNumber);
    context.log('Face Image:', req.body.faceImage);

    // Return a success message if everything is good
    context.res = {
        status: 200,
        body: { success: true, message: 'Data received successfully!' }
    };
};
