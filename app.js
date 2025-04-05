function sendToBackend(imageData, phoneNumber) {
    const data = {
        image: imageData,  // Ensure this is a valid image in base64 format
        phone: phoneNumber // Ensure this is the correct phone number
    };

    console.log("Data being sent:", data);  // Add logging to confirm the data being sent

    fetch('https://attendance-function-app.azurewebsites.net/attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)  // Ensure proper JSON format
    })
    .then(response => response.json())
    .then(data => {
        console.log('Data received:', data);
    })
    .catch((error) => {
        console.error('Error sending data:', error);
    });
}
