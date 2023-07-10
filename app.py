from flask import Flask, render_template, request, redirect, url_for, session
import ibm_db
import os
from clarifai_grpc.grpc.api.status import status_code_pb2
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())
import requests
from flask import request
import json


app = Flask(__name__)
app.secret_key = 'a'
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=9938aec0-8105-433e-8bf9-0fbb7e483086.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32459;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA (6).crt;UID=bnz17181;PWD=Tj5kCYGEKITBhBaT",'','')

# conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=824dfd4d-99de-440d-9991-629c01b3832d.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30119;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA (2).crt;UID=gzt33282;PWD=Ufsj8ideWJk2J3QX", '', '')
print("connected")


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login", methods=["POST", 'GET'])
def login():
    global Userid
    msg = ''

    if request.method == "POST":
        USERNAME = request.form["username"]
        PASSWORD = request.form["password"]
        sql = "SELECT * FROM USERN WHERE  USERNAME=? AND PASSWORD=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, USERNAME)
        ibm_db.bind_param(stmt, 2, PASSWORD)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['Loggedin'] = True
            session['id'] = account['USERNAME']
            Userid = account['USERNAME']
            session['username'] = account['USERNAME']
            msg = "logged in successfully !"
            return render_template('submission.html', msg=msg, name= USERNAME)
        else:
            msg = "Incorrect username/password"
    return render_template('login.html', msg=msg)


@app.route("/register", methods=["POST", 'GET'])
def register():
    msg = ''
    if request.method == 'POST':
        USERNAME = request.form["username"]
        EMAIL = request.form["email"]
        PASSWORD = request.form["password"]
        sql = "SELECT* FROM USERN WHERE USERNAME = ?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, USERNAME)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            msg = 'You have already Exists!'
            return render_template('login.html', msg=msg)
        else:
            insert_sql = "INSERT INTO USERN VALUES (?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, USERNAME)
            ibm_db.bind_param(prep_stmt, 2, EMAIL)
            ibm_db.bind_param(prep_stmt, 3, PASSWORD)
            ibm_db.execute(prep_stmt)
            msg = "You have successfully registered !"
            return render_template('login.html', msg=msg)
    return render_template('register.html', msg=msg)

@app.route('/submission')
def submission():
    return render_template('submission.html')

@app.route('/display', methods=["POST", "GET"])
def display():
    foodName=''
    if request.method == "POST":
        image = request.files["food"] 
        YOUR_CLARIFAI_API_KEY = "51f1d1b150cc467c9a79e1a29ec0709a"
        YOUR_APPLICATION_ID = "Sandeep-project"
        SAMPLE_URL = "https://samples.clarifai.com/metro-north.jpg"

        # This is how you authenticate.
        metadata = (("authorization", f"Key {YOUR_CLARIFAI_API_KEY}"),)

        with open(image.filename, "rb") as f:
            file_bytes = f.read()    
            request1 = service_pb2.PostModelOutputsRequest(
            # This is the model ID of a publicly available General model. You may use any other public or custom model ID.
            model_id="general-image-recognition",
            user_app_id=resources_pb2.UserAppIDSet(app_id=YOUR_APPLICATION_ID),
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes))
                )
            ],
        )
        response = stub.PostModelOutputs(request1, metadata=metadata)

        print(response)

        if response.status.code != status_code_pb2.SUCCESS:
            print(response)
            raise Exception(f"Request failed, status code: {response.status}")

        for concept in response.outputs[0].data.concepts:
            if(concept.value>0.999):
                foodName=concept.name

        print(foodName)
        nutrients = {}
        USDAapiKey = '9f8yGs19GGo5ExPpBj7fqjKOFlXXxkJdMyJKXwG3'
        response = requests.get('https://api.nal.usda.gov/fdc/v1/foods/search?api_key={}&query={}&requireAllWords={}'.format(USDAapiKey, foodName, True))

        data = json.loads(response.text) 
        concepts = data['foods'][0]['foodNutrients']
        arr = ["Sugars","Energy", "Vitamin A","Vitamin D","Vitamin B", "Vitamin C", "Protein","Fiber","Iron","Magnesium",
                "Phosphorus","Cholestrol","Carbohydrate","Total lipid (fat)", "Sodium", "Calcium",]     
        for x in concepts:
            if x['nutrientName'].split(',')[0] in arr:
                if(x['nutrientName'].split(',')[0]=="Total lipid (fat)"):
                    nutrients['Fat'] = str(x['value'])+" " + x['unitName']
                    print(nutrients['Fat'])
                else:
                    nutrients[x['nutrientName'].split(',')[0]] = str(x['value'])+" " +x['unitName']
        print(nutrients)
        return render_template('display.html', x = foodName,data=nutrients, account = session['username'])
    else:
        return render_template('submission.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
