import requests
from shared_variables import urlLogin, urlProduceApiKey, urlUploadSensorData, headers, credentials, patientId, deviceApiKey, sensorDataToUpload 

def login():
    global jwt_token, headers, credentials

    response = requests.post(urlLogin, headers=headers, json=credentials)
    if response.status_code == 200:
        response_data = response.json()
        jwt_token = response_data.get('message')
        print("JWT Token:", jwt_token)
        headers['Authorization'] = jwt_token;
    else:
        print("Failed to authenticate(Login). Status code:", response.status_code)

def get_device_api_key():
    global deviceApiKey, headers, patientId

    response = requests.get(urlProduceApiKey, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        for i in range(len(response_data)):
            if patientId == response_data[i].get('patientId'):
                deviceApiKey = response_data[i].get('apiKey')   # select the corresponding patientId, exerciseId and sessionId
                print("apiKey:", deviceApiKey)
                headers['Authorization'] = deviceApiKey
                headers['Content-Type'] = 'application/json-patch+json'
    else:
        print("Failed to authenticate(get_device_api_key). Status code:", response.status_code)

def upload_sensor_data():
    global deviceApiKey, headers, sensorDataToUpload
    
    response = requests.post(urlUploadSensorData, headers=headers, json=sensorDataToUpload)
    if response.status_code == 200:
        response_data = response.json()
        deviceApiKey = response_data.get('message')  
        print("response of uploading!!!", deviceApiKey)
    else:
        print("Failed to authenticate(upload_Sensor_data). Status code:", response.status_code)