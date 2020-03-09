# Detect License Plate

In this Code Pattern, we will demonstrate how to leverage OCR and the "IBM Visual Insights" object recognition service to identify and read license plates.

This use case is ideal for automated "Gate Access Control" in spaces such as a workplace, apartment complex, or mall parking lot.

When the reader has completed this Code Pattern, they will understand how to
- Build a object detection model
- Trigger a "post processing" script when specific objects are detected
- Leverage Python Opencv libraries to prepare an image for OCR
- Adjust Tesseract OCR to detect specific fonts

<img src="https://developer.ibm.com/developer/patterns/custom-inference-script-for-reading-license-plates-of-cars/images/license-plate-ocr-flow.png">
<!-- ![Architecture](https://i.imgur.com/lKeuzAn.png) -->


#  Components

* [IBM Visual Insights](https://www.ibm.com/products/maximo). This is an image analysis platform that allows you to build and manage computer vision models, upload and annotate images, and deploy apis to analyze images and videos.

Sign up for a trial account of IBM Visual Insights [here](https://developer.ibm.com/linuxonpower/deep-learning-powerai/try-powerai/). This link includes options to provision a IBM Visual Insights instance either locally on in the cloud.


* [Kubernetes](https://cloud.ibm.com/kubernetes/catalog/cluster). Kubernetes is a container orchestration engine. In this case, we'll use Kubernetes to host a python server with OCR libraries. The server will accept images via an HTTP POST request, and process the images to extract and recognize text from an image.

# Flow

1. Photo of car is uploaded to IBM Visual Insights dashboard.
2. Object recognition model identifies location of license plate(s).
3. IBM Visual Insights "Post Processing" script forwards image and object location to custom server.
4. Custom server improves image with following steps:
    - Binarisation (Convert image to black and white)
    - [Edge Detection](https://docs.opencv.org/2.4/doc/tutorials/imgproc/imgtrans/canny_detector/canny_detector.html)
    - [Rotation](https://tesseract-ocr.github.io/tessdoc/ImproveQuality#rotation--deskewing)
    - Border Removal
5. Custom server runs processed images through OCR library.

# Prerequisites

* An account on IBM Marketplace that has access to IBM Visual Insights. This service can be provisioned [here](https://developer.ibm.com/linuxonpower/deep-learning-powerai/vision/access-registration-form/)

<!-- * [Docker Engine](https://docs.docker.com/install/).  -->

# Steps

Follow these steps to setup and run this Code Pattern.

1. [Deploy a Kubernetes Cluster](#1-deploy-a-kubernetes-cluster)
2. [Upload training images to IBM Visual Insights ](#2-upload-training-images-to-powerai-vision)
3. [Train and deploy model in IBM Visual Insights](#3-Train-and-deploy-model-in-PowerAI-Vision)
4. [Clone repository](#4-clone-repository)
5. [Deploy OCR Server](#5-deploy-ocr-server)

<!-- 5. [Create a Dashboard](#4-create-dashboard) -->

## 1. Deploy a Kubernetes Cluster
Create a Kubernetes cluster [here](https://cloud.ibm.com/kubernetes/catalog/cluster/create).

While the cluster is being provisioned, a set of steps will be presented to access the cluster via CLI.

<img src="https://i.imgur.com/dlFFkDs.png" />

<!-- ```
curl -sL https://ibm.biz/idt-installer | bash
``` -->

After completing the steps, click the "Worker Nodes" tab. Take note of the value under "Public IP".

**Important!!**
Set the external IP address as the URL variable in the [custom.py](custom.py#L52) script.

<img src="https://i.imgur.com/p0gTEfD.png" />


## 2. Upload training images to IBM Visual Insights

Login to IBM Visual Insights Dashboard

<img src="https://i.imgur.com/66awAad.png">

To build a model, we'll first need to upload a set of images. Click "Datasets" in the upper menu. Then, click "Create New Data Set", and enter a name. We'll use "ocr" here


<img src="https://i.imgur.com/GcgUKUY.png">


Drag and drop images to build your dataset.

<img src="https://i.imgur.com/rD0sWQN.png">


## 3. Train and deploy model in IBM Visual Insights

In this example, we'll build an object recognition model to identify specific objects in each frame of a video. After the images have completed uploading to the dataset, select one or more images in the dataset, and then select "Label Objects".


<img src="https://i.imgur.com/V3l95SM.png">

<!-- Select "Label Objects"

Select "Auto Capture"

<img src="https://i.imgur.com/DQrZYCW.png"/> -->

Next, we'll split the training video into multiple frames. We'll label objects in a few of the frames manually. After generating a model, we can automatically label the rest of the frames to increase accuracy.


<img src="https://i.imgur.com/XQ7RfC4.png">


Identify what kinds of objects will need to be recognized. Click "Add Label", and type the name of each object. In this case, we're detecting license plates, so we'll create a labels for license plate and cars.

<img src="https://i.imgur.com/DNYgQnU.png">


We can then manually annotate objects by
1. Selecting a video frame
2. Selecting an object type
3. Drawing a rectangle (or custom shape) around object in frame


<img src="https://i.imgur.com/DQrZYCW.png">


After annotating a few frames, we can then build a model. Do so by going back to the "Datasets" view, selecting your dataset, and then selecting "Train Model"

<img src="https://i.imgur.com/Mef0P9b.png">


Select type of Model you'd like to build. In this case, we'll use "Object Detection" as our model type, and "Detectron" as our model optimizer. Then, click the "Train Model" button.


<img src="https://i.imgur.com/YwxC2BA.png">

While the model is training, we'll package our custom inference script as a zip file.
```
zip ocr_process.zip custom.py
```

Then, click "Custom Assets" in the IBM Visual Insights dashboard's upper menu.

Drag and drop the zip file to the section labeled "Release to import asset"


<img src="https://i.imgur.com/qyIhsYB.png"/>

Set the Asset type as "Custom Inference Script" and give it a name.


<img src="https://i.imgur.com/byWQe8f.png" />


After the model completes training, click the "Models" button in the upper menu. Then, select the model and then click the "Deploy Model" button. Be sure to select the custom inference script from the previous step.

<img src="https://i.imgur.com/s171uQl.png">


Deploying the custom model will establish an endpoint where images and videos can be uploaded, either through the UI or through a REST API endpoint.

<img src="https://i.imgur.com/nQkL6qy.png">



## 4. Clone repository

Clone repository using the git cli

```
git clone https://github.com/IBM/license-plate-ocr
```

## 5. Deploy OCR Server

Deploy our OCR server on kubernetes by running the following command
```
kubectl apply -f kubernetes/kube-config.yml
```


Confirm the service and pod is running with the `kubectl get pods,services` command. The output should look like so.

```
Kalonjis-MacBook-Pro:tmp kkbankol@us.ibm.com$ kubectl get pods,services
NAME             READY   STATUS    RESTARTS   AGE
pod/ubuntu-ocr   1/1     Running   0          15h

NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/api-service   NodePort    172.21.216.111   <none>        8000:30001/TCP   15h
service/kubernetes    ClusterIP   172.21.0.1       <none>        443/TCP          25d
```

Once we've confirmed that the server is up and running, test the process by running the following in one tab.
```
kubectl logs -f ubuntu-ocr
```


In your browser, navigate back to the "ocr" model we trained in step 3. Drag and drop an image to the section labeled "Drop image or video here". The results should look like so

<img src="https://i.imgur.com/yhqjnXR.png" />



Our server backend output should look like the following. We have a json array of detected objects, as well as the processed OCR prediction

```
starting server on port 8000
length: 32562012
10.77.223.246 - - [11/Feb/2020 16:47:56] "POST / HTTP/1.1" 200 -
[{'confidence': 0.9984619617462158, 'ymax': 918, 'label': 'car', 'xmax': 1418, 'xmin': 409, 'ymin': 257, 'polygons': [[[751, 244], [679, 292], [499, 292], [463, 315], [427, 315], [391, 339], [391, 859], [427, 882], [463, 882], [535, 930], [1292, 930], [1400, 859], [1364, 835], [1364, 788], [1400, 764], [1364, 741], [1400, 717], [1364, 693], [1364, 646], [1436, 599], [1436, 386], [1364, 339], [1364, 315], [1328, 292], [1292, 292], [1256, 268], [1220, 268], [1184, 292], [1148, 292], [1076, 244]]]}, {'confidence': 0.9999994039535522, 'ymax': 664, 'label': 'license_plate', 'xmax': 1216, 'xmin': 1054, 'ymin': 557, 'polygons': [[[1063, 554], [1051, 562], [1051, 616], [1063, 623], [1057, 627], [1063, 631], [1051, 639], [1051, 654], [1069, 666], [1144, 666], [1156, 658], [1162, 662], [1167, 658], [1196, 658], [1208, 650], [1214, 654], [1220, 650], [1220, 562], [1208, 554]]]}]
{'result': 'BFGYGQ6'}
```

The server will also generate an image showing the different post-processing steps. This shows the following images
- Original cropped/rotated image
- Binary image with borders removed
- Image with edges highlighted (Canny algorithm)
- Final processed image with noise removed

<img src="https://i.imgur.com/FTFQART.png" />


<!-- Run the following to execute the OCR script locally

./ocr_server.py <path_to_local_image> -->

# Learn more

<!-- * **Watson IOT Platform Code Patterns**: Enjoyed this Code Pattern? Check out our other [Watson IOT Platform Code Patterns](https://developer.ibm.com/?s=Watson+IOT+Platform). -->

<!-- * **Knowledge Center**:Understand how this Python function can load data into  [Watson IOT Platform Analytics](https://www.ibm.com/support/knowledgecenter/en/SSQP8H/iot/analytics/as_overview.html) -->

# License

This code pattern is licensed under the Apache Software License, Version 2.  Separate third party code objects invoked within this code pattern are licensed by their respective providers pursuant to their own separate licenses. Contributions are subject to the [Developer Certificate of Origin, Version 1.1 (DCO)](https://developercertificate.org/) and the [Apache Software License, Version 2](https://www.apache.org/licenses/LICENSE-2.0.txt).

[Apache Software License (ASL) FAQ](https://www.apache.org/foundation/license-faq.html#WhatDoesItMEAN)
