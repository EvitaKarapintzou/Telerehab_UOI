# Define shared variables
jwt_token = ""

patientId = 1
sessionId = 5
exerciseId = 1
deviceApiKey = ""

pureApi = "https://telerehab-develop.biomed.ntua.gr/api"
#APIs
urlLogin = pureApi + '/Login'
urlProduceApiKey = pureApi + '/PatientDeviceSet/list'
urlUploadSensorData = pureApi + '/SensorData'
urlGetSchedule = pureApi + '/PatientSchedule'

headers = {
    'accept': '*/*',
    'Content-Type': 'application/json-patch+json',
}
credentials = {
    "username": "testDoctor",
    "password": "TeleAdmin2023"
}
