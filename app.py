from flask import Flask, jsonify, render_template, request
import time
import paho.mqtt.client as mqtt
import mysql.connector
import json

app = Flask(__name__)

# Database connection using your credentials
db_connection = mysql.connector.connect(
    host="sql12.freemysqlhosting.net",
    user="sql12739845",
    password="AIsALCKH8Z",
    database="sql12739845",
    port=3306
)

cursor = db_connection.cursor()

# Store the steps, fall detection, and MQTT status
step_data = {
    "steps": 0,
    "total_steps_10s": 0,
    "total_steps_overall": 0,
    "fall_detected": False,
    "activity": "Not Moving",  # Activity can be "Not Moving", "Walking", "Running"
    "mqtt_status": "Disconnected",
    "last_reset": time.time()
}

# MQTT broker settings
MQTT_BROKER = "5f474025409c4b7588c11fbc1c3dffcb.s1.eu.hivemq.cloud"
MQTT_PORT = 8884  # WebSocket port
MQTT_TOPIC = "esp32/stepcounter"
MQTT_USER = "hivemq.webclient.1729593331255"
MQTT_PASS = "QoS@.4Obqk983V,:xBKa"

# Function to classify activity based on step count
def classify_activity(step_count):
    if step_count == 0:
        return "Not Moving"
    elif step_count <= 10:
        return "Walking"
    else:
        return "Running"

# Function to handle incoming MQTT messages
def on_message(client, userdata, message):
    global step_data
    print(f"Message received: {message.payload.decode()}")
    try:
        step_info = json.loads(message.payload.decode())
        step_data["steps"] = step_info.get("steps", 0)
        step_data["fall_detected"] = step_info.get("fall_detected", False)

        # Classify activity
        step_data["activity"] = classify_activity(step_data["steps"])

        # Update step data
        step_data["total_steps_overall"] += step_data["steps"]
        step_data["total_steps_10s"] += step_data["steps"]

        # Insert step data into the existing steps_data table in MySQL
        try:
            cursor.execute('''
                INSERT INTO steps_data (steps, activity, fall_detected, timestamp) 
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ''', (step_data["steps"], step_data["activity"], step_data["fall_detected"]))
            db_connection.commit()
            print(f"Inserted steps: {step_data['steps']}, activity: {step_data['activity']}, fall: {step_data['fall_detected']}")

        except Exception as e:
            print(f"Error inserting data into database: {e}")

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# MQTT connection handling
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        step_data["mqtt_status"] = "Connected"
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

# Initialize the MQTT client and subscribe to the topic
def mqtt_subscribe():
    client = mqtt.Client(transport="websockets")
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to get the current activity, total step count, fall detection, and MQTT status
@app.route('/api/get-activity', methods=['GET'])
def get_activity():
    return jsonify({
        "steps": step_data["total_steps_overall"],
        "fall_detected": step_data["fall_detected"],
        "activity": step_data["activity"],
        "mqtt_status": step_data["mqtt_status"]
    })

# Endpoint to fetch daily step count from the existing steps_data table
@app.route('/api/get-daily-steps', methods=['GET'])
def get_daily_steps():
    try:
        cursor.execute('''
            SELECT SUM(steps) FROM steps_data WHERE DATE(timestamp) = CURDATE();
        ''')
        result = cursor.fetchone()
        daily_steps = result[0] if result[0] is not None else 0
        print(f"Daily steps fetched: {daily_steps}")
        return jsonify({
            "daily_steps": daily_steps
        })
    except Exception as e:
        print(f"Error fetching daily steps: {e}")
        return jsonify({"error": "Failed to fetch daily steps"}), 500

if __name__ == '__main__':
    mqtt_subscribe()
    app.run(host='0.0.0.0', port=5000)
