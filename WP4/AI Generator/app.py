from crypt import methods
from flask import Flask,jsonify,request
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
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

@app.route("/ping")
def home():
    return jsonify({
        "Message": "app up and running successfully"
    })

@app.route("/optimal_intervation_plan_prediction",methods=["POST"])
def optimal_intervation_plan_prediction():
    data = request.get_json()
    print(data)
    input = data.get("patient_onboarding_data(baseline)", "string")

    message = "low tech or high tech class explainable information."

    return jsonify({
        "Message": message
    })

@app.route("/next_weeks_program",methods=["POST"])
def next_weeks_program():
    data = request.get_json()
    print(data)
    input = data.get("patient baseline data", "string")

    message = "exercise results of previous week."

    return jsonify({
        "Message": message
    })

@app.route("/risk_of_falls1",methods=["POST"])
def risk_of_falls1():
    data = request.get_json()
    print(data)
    input = data.get("baseline", "string")

    message = "probability."

    return jsonify({
        "Message": message
    })

@app.route("/risk_of_falls2",methods=["POST"])
def risk_of_falls2():
    data = request.get_json()
    print(data)
    input = data.get("baseline", "string")

    message = "probability."

    return jsonify({
        "Message": message
    })

@app.route("/risk_of_falls3",methods=["POST"])
def risk_of_falls3():
    data = request.get_json()
    print(data)
    input = data.get("baseline", "string")

    message = "probability."

    return jsonify({
        "Message": message
    })


if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)
