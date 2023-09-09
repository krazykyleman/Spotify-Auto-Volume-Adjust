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
