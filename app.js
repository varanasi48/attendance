// Access the webcam and display the video feed
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');

// Start the video feed from the webcam
navigator.mediaDevices.getUserMedia({ video: true })
    .then((stream) => {
        video.srcObject = stream;
    })
    .catch((error) => {
        console.log("Error accessing webcam:", error);
    });

// Capture the image and send to backend
function captureFace() {
    // Draw the image on the canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert the canvas image to a base64 string
    let imageData = canvas.toDataURL('image/jpeg'); // includes prefix
    imageData = imageData.replace(/^data:image\/jpeg;base64,/, ''); // remove prefix

    // Get the phone number from the input field
    const phoneNumber = document.getElementById('phone').value;

    // Send the data to the backend
    sendToBackend(imageData, phoneNumber);
}

// Function to send the captured image and phone number to the backend
function sendToBackend(imageBase64, phoneNumber) {
    const data = {
        faceImageBase64: imageBase64,
        phoneNumber: phoneNumber
    };

    fetch('https://attendance-function-app.azurewebsites.net/backend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Server response:', data);
        alert(data.message || 'Success!');
    })
    .catch((error) => {
        console.error('Error sending data:', error);
        alert('Error sending data to server.');
    });
}
