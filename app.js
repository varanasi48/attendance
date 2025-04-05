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
    const imageData = canvas.toDataURL('image/jpeg');
    
    // Get the phone number from the input field
    const phoneNumber = document.getElementById('phone').value;
    
    // Check if phone number is valid
    if (!phoneNumber) {
        console.error("Phone number is required");
        return;
    }

    // Send the data to the backend
    sendToBackend(imageData, phoneNumber);
}

// Function to send the captured image and phone number to the backend
function sendToBackend(imageData, phoneNumber) {
    const data = {
        image: imageData,
        phone: phoneNumber
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
        if (data.success) {
            alert('Attendance marked successfully!');
        } else {
            alert('Failed to mark attendance!');
        }
    })
    .catch((error) => {
        console.error('Error sending data:', error);
    });
}
