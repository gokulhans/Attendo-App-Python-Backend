from flask import Flask, request, jsonify
import face_recognition as fr
from pymongo import MongoClient
import numpy as np
from datetime import datetime
import pytz
from flask_cors import CORS

def get_database():
    CONNECTION_URL = "mongodb+srv://govi:govi@cluster0.qmc6cnq.mongodb.net/Attendoappdev?retryWrites=true&w=majority&appName=Cluster0"  # Update this with your connection URL
    client = MongoClient(CONNECTION_URL)
    return client['Attendoappdev']
    
def getEncodings():
    dbname = get_database()
    collection_name = dbname["encodings"]
    items = collection_name.find({})
    known_images = []
    encodings = []
    
    for item in items:
        item.pop("_id")
        employee_id = item["employee_id"]
        encoding = np.array(item["encoding"])
        known_images.append(employee_id)
        encodings.append(encoding)
    
    return known_images, encodings

def update_face(employeeId, addImg):
    addImage = fr.load_image_file(addImg)
    try:
        image_encoding = list(fr.face_encodings(addImage)[0])
    except IndexError as e:
        return False
    
    try:
        # Store with employee_id as reference instead of filename
        data = {
            "employee_id": employeeId,
            "encoding": image_encoding,
            "created_at": datetime.now().isoformat()
        }
        
        dbname = get_database()
        collection_name = dbname["encodings"]
        
        # Check if employee already has encoding and update it
        existing = collection_name.find_one({"employee_id": employeeId})
        if existing:
            collection_name.update_one(
                {"employee_id": employeeId}, 
                {"$set": {"encoding": image_encoding, "updated_at": datetime.now().isoformat()}}
            )
        else:
            collection_name.insert_one(data)
        
        return True
    except Exception as e:
        print("Error saving encoding:", e)
        return False

def compare_faces(baseImg):
    known_images, encodings = getEncodings()
    if not known_images or not encodings:
        return False
        
    test = fr.load_image_file(baseImg)
    try:
        test_encoding = fr.face_encodings(test)[0]
    except IndexError as e:
        return False
        
    results = fr.compare_faces(encodings, test_encoding)    
    print(results)
    if(True in results):
        i = results.index(True)
        return known_images[i]  # Return the employee_id directly
    return False

def update_attendance(employee_id, status):
    """
    Update attendance records for an employee
    
    Args:
        employee_id: The ID of the employee
        status: The status of the attendance (present, late, etc.)
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        IST = pytz.timezone('Asia/Kolkata')
        now = datetime.now(IST)
        
        # Store dates in a standardized format for easier querying
        today_date = now.strftime("%Y-%m-%d")  # ISO format for date
        current_time = now.strftime("%H:%M:%S")
        
        # Get database and collection for attendance
        db = get_database()
        users_collection = db["users"]
        # Use a dedicated collection for all attendance records
        collection_name = db["attendances"]

        # Fetch user details from users collection
        user = users_collection.find_one({"employeeId": employee_id})
        if not user:
            print(f"User not found with employee_id: {employee_id}")
            return False
        
        # Create attendance record with more detail
        data = {
            "employee_id": str(user["_id"]),  # Convert ObjectId to string,
            "status": status,
            "date": today_date,
            "time": current_time,
            "timestamp": datetime.now().isoformat(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute
        }
        
        # Insert the attendance record
        result = collection_name.insert_one(data)
        
        print(f"Attendance updated for employee {employee_id}: {status}")
        return True
    except Exception as e:
        print(f"Error updating attendance: {e}")
        return False

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route('/face_match', methods=['POST'])
def face_match():
    if request.method == 'POST':
        if ('file1' in request.files):  
            file1 = request.files.get('file1')                   
            response = compare_faces(file1)  
            if response:
                employee_id = response
                status = request.form.get('status', 'present')  # Default to 'present' if not provided
                update_attendance(employee_id, status)
            return jsonify({"status": bool(response), "employee_id": response}) 
        return jsonify({"status": False, "message": "No image file provided"})

@app.route('/add_face', methods=['POST'])
def add_face():
    if request.method == 'POST':
        if ('file1' in request.files):
            file1 = request.files.get('file1')
            # Get employee ID from form data or from filename
            employee_id = request.form.get('employee_id', file1.filename.split(".")[0])
            print(f"Adding face for employee: {employee_id}")
            
            response = update_face(employee_id, file1)
            return jsonify({"status": response, "employee_id": employee_id})
        return jsonify({"status": False, "message": "No image file provided"})

@app.route('/', methods=['GET'])
def home():
    return 'AttendEase APP API'

if __name__ == '_main_':
    app.run(host='0.0.0.0', port=5002, debug=True)