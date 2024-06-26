import requests
import datetime 

from shared_variables import urlLogin, urlProduceApiKey, urlGetSchedule, headers, credentials, patientId, deviceApiKey 

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

def get_schedule(patientId):
    global deviceApiKey, headers, jwt_token
    
    headers['Authorization'] = jwt_token  # prepei na fugei

    response = requests.get(urlGetSchedule + '/' + patientId + '/list', headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        schedule = response_data[0]['schedule']
        weekNumber = response_data[0]['weekNumber']
        activityType = response_data[0]['activityType']
        studyWeek = response_data[0]['studyWeek']
        schedule_info = []
        schedule_info.append("patientId " + str(patientId))
        for item in schedule:
            schedule_info.append("dayNumber " + str(item['dayNumber']) + " exerciseId " + str(item['exerciseId']))
        schedule_info.append("weekNumber " + str(weekNumber) + " activityType " + str(activityType) + " studyWeek " + str(studyWeek))
        schedule_str = " ".join(schedule_info)
        #schedule_str = schedule_info + "\n"
        with open("/home/christoforos/Documents/GitHub/Telerehab_UOI/WP3/scheduler/schedule.txt", "a") as file:
            file.write(schedule_str)
    else:
        return "Failed to authenticate(upload_Sensor_data). Status code:" + str(response.status_code)

login()
get_device_api_key()
get_schedule("1")

