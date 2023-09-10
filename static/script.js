document.getElementById('startButton').addEventListener('click', function() {
    let volume = document.getElementById('volumeAdjustment').value;
    fetch('/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({volume: volume})
    })
    .then(response => response.json())
    .then(data => {
        console.log("Received response:", data);
        
        // Check if the volume controller started successfully
        if (data.success) {
            alert('Volume controller started successfully.');
        } else {
            alert('An error occurred while starting the volume controller: ' + data.message);
        }
    })
    
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
    
});

document.getElementById('authButton').addEventListener('click', function() {
    authorizeSpotify();
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
    // Display the waiting message
    document.getElementById('statusMessage').textContent = 'Waiting for Authorization...';

    fetch('/authorize')
       .then(response => response.json())
        .then(data => {
            console.log(data);
            //Handle the response from the Flask server
           if (data.success) {
                //If authorization is successful, redirect to the Spotify authorization URL
               window.location.href = data.auth_url;
            } else {
                //Handle any errors or issues
               alert('Authorization failed. Please try again.');
            }
        })
        .catch(error => {
            //Handle any network or request errors
           console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
}