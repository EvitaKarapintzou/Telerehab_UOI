from crypt import methods
from flask import Flask,jsonify,request
from flask_swagger_ui import get_swaggerui_blueprint
import sys
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SWAGGER_URL="/swagger"
API_URL="/static/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'AI Generator API'
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/ping")
def home():
    return jsonify({
        "Message": "app up and running successfully"
    })

@app.route("/optimal_intervation_plan_prediction", methods=["POST"])
def optimal_intervation_plan_prediction():
    data = request.get_json()
    input_data = data.get("Age", 35)
    return jsonify({
        "output": 345
    })

@app.route("/next_weeks_program",methods=["POST"])
def next_weeks_program():
    data = request.get_json()
    print(data)
    input = data.get("patient baseline data", "string") #excel

    message = "updated program." #json   {"nextExcersises": [1,2,3,4]}

    return jsonify({
        "Message": message
    })

@app.route("/risk_of_falls1",methods=["POST"])
def risk_of_falls1():
    data = request.get_json()
    print(data)
    input = data.get("baseline", "string")  #excel

    message = "probability."   #double

    return jsonify({
        "Message": message
    })

@app.route("/risk_of_falls2",methods=["POST"])
def risk_of_falls2():
    data = request.get_json()
    print(data)
    input = data.get("baseline", "string")  #excel

    message = "treatment effect and side effects." #json {"level": 5}

    return jsonify({
        "Message": message
    })

@app.route("/risk_of_falls3",methods=["POST"])
def risk_of_falls3():
    data = request.get_json()
    print(data)
    input = data.get("baseline", "string")  #excel

    message = "problems side effects."   #json {"level": 5}

    return jsonify({
        "Message": message
    })


if __name__=="__main__":
    url = os.getenv('URL', 'http://0.0.0.0:8080')
    host = url.split('//')[1].split(':')[0]
    port = int(url.split(':')[-1])
    app.run(host=host, port=port)