// Function to submit user details
function submitUserDetails() {
    const age = document.getElementById('age').value;
    const gender = document.getElementById('gender').value;

    fetch('/api/user-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ age: age, gender: gender })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    });
}

// Function to fetch the latest step data and activity
function fetchActivity() {
    fetch('/api/get-activity')
    .then(response => response.json())
    .then(data => {
        document.getElementById('stepCount').textContent = data.steps;
        document.getElementById('activity').textContent = data.activity;
    });
}


// Refresh the activity every 10 seconds
setInterval(fetchActivity, 10000);

// Initial load
fetchActivity();
