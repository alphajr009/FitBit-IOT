from flask import Flask, jsonify, render_template
import time
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Store the steps, user details, and WiFi status
step_data = {
    "steps": 0,  # Current step count (received from ESP32 via MQTT)
    "total_steps_10s": 0,  # Steps in the current 10-second window (for activity classification)
    "total_steps_overall": 0,  # Total accumulated steps over time
    "age": None,
    "gender": None,
    "activity": "Not Moving",
    "wifi_status": "Disconnected",  # Default WiFi status
    "last_reset": time.time()
}

# MQTT broker settings (replace with your HiveMQ credentials)
MQTT_BROKER = "5f474025409c4b7588c11fbc1c3dffcb.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "esp8266/stepcounter"
MQTT_USER = "alphawefit"
MQTT_PASS = "Alpha@2024"


# Activity classification logic based on step count
def classify_activity(step_count):
    if step_count == 0:
        return "Not Moving"
    elif step_count <= 10:
        return "Walking"
    elif step_count <= 20:
        return "Jogging"
    else:
        return "Running"


# MQTT message handling function (called when a message is received)
def on_message(client, userdata, message):
    global step_data
    print(f"Message received: {message.payload.decode()}")
    # Assume the payload is in JSON format with "steps" field
    try:
        step_info = json.loads(message.payload.decode())
        step_count = step_info.get("steps", 0)

        # Update step data
        step_data["total_steps_overall"] += step_count
        step_data["total_steps_10s"] += step_count

        # Check if 10 seconds have passed and classify activity
        if time.time() - step_data["last_reset"] >= 10:
            step_data["activity"] = classify_activity(step_data["total_steps_10s"])
            step_data["total_steps_10s"] = 0
            step_data["last_reset"] = time.time()

    except Exception as e:
        print(f"Error processing MQTT message: {e}")


# Initialize the MQTT client and connect to the broker
def mqtt_subscribe():
    client = mqtt.Client()
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()  # Enable SSL/TLS for secure connection
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Subscribe to the topic
    client.subscribe(MQTT_TOPIC)
    client.loop_start()


@app.route('/')
def index():
    return render_template('index.html')


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
    mqtt_subscribe()  # Start subscribing to MQTT messages
    app.run(host='0.0.0.0', port=5000)
