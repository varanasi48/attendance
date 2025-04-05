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
function sendToBackend(imageData, phoneNumber) {
    const data = {
        image: imageData,
        phone: phoneNumber
    };

    // Log the data being sent
    console.log('Sending data to backend:', data);

    // Use fetch API to send data to your backend (Azure Function/API)
    fetch('https://attendance-function-app.azurewebsites.net/attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Data received:', data);
    })
    .catch((error) => {
        console.error('Error sending data:', error);
    });
}

