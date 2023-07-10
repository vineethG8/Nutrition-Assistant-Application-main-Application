from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2


import requests
import json

def imagedetection():
    YOUR_CLARIFAI_API_KEY = "51f1d1b150cc467c9a79e1a29ec0709a"
    YOUR_APPLICATION_ID = "Sandeep-project"
    SAMPLE_URL = "https://samples.clarifai.com/metro-north.jpg"

    # This is how you authenticate.
    metadata = (("authorization", f"Key {YOUR_CLARIFAI_API_KEY}"),)

    with open("piza.png", "rb") as f:
        file_bytes = f.read()    
    request = service_pb2.PostModelOutputsRequest(
        # This is the model ID of a publicly available General model. You may use any other public or custom model ID.
        model_id="general-image-recognition",
        user_app_id=resources_pb2.UserAppIDSet(app_id=YOUR_APPLICATION_ID),
        inputs=[
            resources_pb2.Input(
                data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes))
            )
        ],
    )
    response = stub.PostModelOutputs(request, metadata=metadata)

    if response.status.code != status_code_pb2.SUCCESS:
        print(response)
        raise Exception(f"Request failed, status code: {response.status}")

    for concept in response.outputs[0].data.concepts:
        if(concept.value>0.99):
            return concept.name
        print("%12s: %.2f" % (concept.name, concept.value))
        
foodName=imagedetection()

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





