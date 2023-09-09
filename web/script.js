document.getElementById('startButton').addEventListener('click', function() {
    let volume = document.getElementById('volumeAdjustment').value;
    eel.start(volume); // Call the start Python function
});

document.getElementById('authButton').addEventListener('click', function() {
    eel.start_flask(); // Call the start_flask Python function
});
mdc.autoInit();

const volumeAdjustment = document.getElementById('volumeAdjustment');
document.getElementById('volumeAdjustment').addEventListener('input', function() {
    const label = document.getElementById('my-label');
    if (this.value) {
        label.style.display = 'none';
    } else {
        label.style.display = 'block';
    }
});

function authorizeSpotify() {
    // Make an AJAX request to the Flask server to initiate authorization
    fetch('http://127.0.0.1:8080/')
        .then(response => response.json())
        .then(data => {
            // Handle the response from the Flask server
            if (data.success) {
                // If authorization is successful, redirect to the Spotify authorization URL
                window.location.href = data.auth_url;
            } else {
                // Handle any errors or issues
                alert('Authorization failed. Please try again.');
            }
        })
        .catch(error => {
            // Handle any network or request errors
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
}

