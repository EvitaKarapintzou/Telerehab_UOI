# Define shared variables
jwt_token = ""

patientId = 1
sessionId = 5
exerciseId = 1
deviceApiKey = ""

#APIs
urlLogin = 'https://telerehab-develop.biomed.ntua.gr/api/Login'
urlProduceApiKey = 'https://telerehab-develop.biomed.ntua.gr/api/PatientDeviceSet/list'
urlUploadSensorData = 'https://telerehab-develop.biomed.ntua.gr/api/SensorData'
urlGetSchedule = 'https://telerehab-develop.biomed.ntua.gr/api/PatientSchedule'

headers = {
    'accept': '*/*',
    'Content-Type': 'application/json-patch+json',
}
credentials = {
    "username": "testDoctor",
    "password": "TeleAdmin2023"
}
