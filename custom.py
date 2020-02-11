# from PIL import Image
# import pytesseract
# import cv2
import os
import requests
import json
import shutil
import sys
class CustomInference:
    # Callout for inference pre-processing.  Will be called before the
    # actual inference on the "image"
    #
    # Input:
    #    image:    Image represented as a NumPy array that inference is to be
    #              performed on.
    #
    #params:  To be used for additional parameters.  This will be
    #             a listof key/value pairs.
    #
    # Output:
    #    image:    Return the image represented as a NumPy array that is to
    #              be used for inference.  This array may been manipulated
    #              in this function, or it may be the same exact NumPy array.
    #
    def onPreProcessing(self, image, params):
        return image
    # Callout for the inference post-processing.  Will be called
    # after the image has been inferred.
    #
    # Input:
    #    Image:    Image represented as a NumPy array that inference is to be
    #              performed on.
    #
    #results:  JSON of the inference results.  The JSON will be
    #              dependent on thetype of inference.
    #
    #params: To be used for additional parameters.  This will
    #              be a list of key/value pairs
    #
    # Output:
    #    results:  A json object that is a copy of the original
    #              inference results.  However, if the callout
    #              intends to return additional information, that
    #              information can bereturnedin the json results
    #              under the key "user".
    #
    def onPostProcessing(self, image, results, params):
         print("onPostProcessing image.shape")
         print(image.shape)
         print("onPostProcessing results")
         print(results)
         # url = "http://127.0.0.1:8000"
         try:
             payload = {'results': results, 'image': image.tolist()}
             print("posting payload")
             r = requests.post(url, json=payload, timeout=120)
             print("status")
             print(r)
         except Exception as inst:
             print(inst)
         return results

# def zip_image(image):
     # path = "./results"
     # if not os.path.exists(path):
     #     os.mkdir(path)
     # cv2.imwrite('./results/output.png', image)
     # shutil.make_archive('./results/inference_data', 'zip',  './results/')
     # f = open("results/inference_data.zip", 'rb')
     # files = {'inference_data.zip': f}
     # payload = {'file':  {  "inference_data.zip"} }
     # files={"archive": ("test.zip", fileobj)})
     # print("onPostProcessing payload")
     # r = requests.post(url, files=files)
