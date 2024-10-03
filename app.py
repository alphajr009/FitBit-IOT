from flask import Flask, request, jsonify, render_template
import time
import joblib
import pandas as pd

app = Flask(__name__)

# Load the pre-trained model and label encoders
model = joblib.load('./models/activity_classification_model.pkl')
gender_encoder = joblib.load('./models/gender_label_encoder.pkl')
activity_encoder = joblib.load('./models/activity_label_encoder.pkl')

# Store the steps and user details
step_data = {
    "steps": 0,  # Current step count (received from ESP32)
    "total_steps_10s": 0,  # Steps in the current 10-second window (used for activity classification)
    "total_steps_overall": 0,  # Total accumulated steps over time
    "age": None,
    "gender": None,
    "activity": "Not Moving",
    "last_reset": time.time()
}


# Use the machine learning model to classify the activity
def classify_activity_ml(step_count, age, gender):
    if age is None or gender is None:
        return "Unknown"

    # Create a DataFrame with the step count, age, and encoded gender
    df = pd.DataFrame([[step_count, age, gender]], columns=['steps_10s', 'age', 'gender'])

    # Encode the gender using the pre-trained encoder
    df['gender'] = gender_encoder.transform([gender])[0]  # Encode gender as 0 (Female) or 1 (Male)

    # Predict the activity using the pre-trained model
    activity_pred = model.predict(df)[0]

    # Decode the predicted activity back to its label
    activity_label = activity_encoder.inverse_transform([activity_pred])[0]

    return activity_label


@app.route('/')
def index():
    return render_template('index.html')


# Endpoint to receive step data from ESP32
@app.route('/api/step-data', methods=['POST'])
def receive_step_data():
    global step_data
    data = request.json
    step_count = data.get("steps", 0)

    # Accumulate total steps over time (without resetting)
    step_data["total_steps_overall"] += step_count

    # Add steps to the 10-second interval for classification
    step_data["total_steps_10s"] += step_count

    # Check if 10 seconds have passed
    if time.time() - step_data["last_reset"] >= 10:
        # Use the trained machine learning model to classify the activity
        step_data["activity"] = classify_activity_ml(
            step_data["total_steps_10s"],
            step_data["age"],
            step_data["gender"]
        )

        # Reset the 10-second interval for the next cycle
        step_data["total_steps_10s"] = 0
        step_data["last_reset"] = time.time()

    return jsonify({"message": "Step data received", "activity": step_data["activity"]}), 200


# Endpoint to get the current activity and total step count (for frontend display)
@app.route('/api/get-activity', methods=['GET'])
def get_activity():
    # Return the accumulated steps and current activity
    return jsonify({
        "steps": step_data["total_steps_overall"],  # Show total accumulated steps
        "activity": step_data["activity"]  # Show current activity
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
