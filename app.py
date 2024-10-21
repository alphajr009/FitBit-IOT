from flask import Flask, request, jsonify, render_template
import time

app = Flask(__name__)

# Store the steps, user details, and WiFi status
step_data = {
    "steps": 0,  # Current step count (received from ESP32)
    "total_steps_10s": 0,  # Steps in the current 10-second window (used for activity classification)
    "total_steps_overall": 0,  # Total accumulated steps over time
    "age": None,
    "gender": None,
    "activity": "Not Moving",
    "last_reset": time.time(),
    "wifi_status": "Disconnected"  # WiFi status
}


# Classification logic based on step count
def classify_activity(step_count):
    if step_count == 0:
        return "Not Moving"
    elif step_count <= 10:
        return "Walking"
    elif step_count <= 20:
        return "Jogging"
    else:
        return "Running"


@app.route('/')
def index():
    return render_template('index.html')


# Endpoint to receive step data from ESP32 (also includes WiFi status)
@app.route('/api/step-data', methods=['POST'])
def receive_step_data():
    global step_data
    data = request.json
    step_count = data.get("steps", 0)
    wifi_status = data.get("wifi_status", "Disconnected")

    # Update WiFi status
    step_data["wifi_status"] = wifi_status

    # Accumulate total steps over time (without resetting)
    step_data["total_steps_overall"] += step_count

    # Add steps to the 10-second interval for classification
    step_data["total_steps_10s"] += step_count

    # Check if 10 seconds have passed
    if time.time() - step_data["last_reset"] >= 10:
        # Classify activity based on steps in the last 10 seconds
        step_data["activity"] = classify_activity(step_data["total_steps_10s"])

        # Reset the 10-second interval for the next cycle
        step_data["total_steps_10s"] = 0
        step_data["last_reset"] = time.time()

    return jsonify({"message": "Step data received", "activity": step_data["activity"], "wifi_status": step_data["wifi_status"]}), 200


# Endpoint to get the current activity, total step count, and WiFi status (for frontend display)
@app.route('/api/get-activity', methods=['GET'])
def get_activity():
    # Return the accumulated steps, current activity, and WiFi status
    return jsonify({
        "steps": step_data["total_steps_overall"],
        "activity": step_data["activity"],
        "wifi_status": step_data["wifi_status"]
    })


# Endpoint to receive user details (age and gender)
@app.route('/api/user-details', methods=['POST'])
def set_user_details():
    global step_data
    data = request.json
    step_data["age"] = data.get("age", None)
    step_data["gender"] = data.get("gender", None)
    return jsonify({"message": "User details updated"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
