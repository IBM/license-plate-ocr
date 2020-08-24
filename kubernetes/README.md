# Secrets

* Secrets contain small amount of sensitive data.
    * Passwords, Tokens or Keys.
* Reduces risk of exposing sensitive data.
* Created outside of Pods.
* Stored inside ETCD database on Kubernetes Master.
* Not more than 1MB.
* Used in two ways - Volumes or Env variables.
* Sent only to the target nodes. 

## 1. Generate Credentials 

In order to connect to IBM DB2 on Cloud, we require a set of credentials.
The credentials are required in `db2_script.py` file as it makes an authentication request to generate a token - which 
is then used to execute sql commands.

1. Generate a set of credentials.
2. Store them in a text file.

## 2. Creating Secrets - Using Kubectl

### 2.1. Syntax 
```
---------------------------------------------
kubectl create secret [TYPE] [NAME] [Data]
---------------------------------------------
Type:
    1. generic
        * File
        * Directory
        * Literal Value
    
    2. docker-registry

    3. tls

Data:
    1. Path to dir/file:    --from-file
        * Used to pass in single or multiple files 
        * Pass in directory containing multiple files

    2. Key-Value pair  :    --from-literal
        * Used to pass key-value pairs from command line
```

We already have a `credentials.txt` containing all the required credentials.
Let's create a secret and name it `db2-credentials` where we will pass our credentials.

### 2.2. Creating Secret 
1. Creating a secret:
    ```commandline
    kubectl create secret generic db2-credentials --from-file=./kubernetes/credentials.txt
    ```
    Output (on success):
    ```
    secret/db2-credentials created
    ```

2. Display secret:
    ```commandline
    kubeclt get secrets
    ```
   Output:
   ```
   NAME                             TYPE            DATA            AGE
   db2-credentials                  Opaque          1               3m
   ```

3. Get complete details of a specific secret:
    ```commandline
    kubectl describe secrets db2-credentials
    ```
   Output:
   ```yaml
    Name:         db2-credentials
    Namespace:    default
    Labels:       <none>
    Annotations:  <none>
    
    Type:  Opaque
    
    Data
    ====
    credentials.txt:  965 bytes
   ```
   The actual credentials are not displayed anywhere.

4. Generate yaml file (not necessary - just to examine)
    ```commandline
     kubectl get secrets db2-credentials -o yaml
    ```
   Output:
   ```
    apiVersion: v1
    data:
        credentials.txt: <base 64 encoded credentials>
    kind: Secret
    metadata:
      creationTimestamp: "2020-08-24T07:20:25Z"
      name: db2-credentials
      namespace: default
      resourceVersion: "9120866"
      selfLink: /api/v1/namespaces/default/secrets/db2-credentials
      uid: 86a688d1-4b06-47bc-aaab-1e2257bbcd99
    type: Opaque
   ```
   You will notice that the credentials are Base64 encoded.

## 3. Using Secrets - Env Variables

To use a secret in an environment variable in a Pod:

1. Create a secret or use an existing one. Multiple Pods can reference the same secret.
2. Modify your Pod definition in each container that you wish to consume the value of a secret key to add an environment 
   variable for each secret key you wish to consume. The environment variable that consumes the secret key should 
   populate the secret's name and key in `env[].valueFrom.secretKeyRef`.
3. Modify your image and/or command line so that the program looks for values in the specified environment variables.

Modified kube-config.yml:
```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    srv: api
  name: ubuntu-ocr
spec:
  containers:
    - name: ubuntu-ocr
      image: kkbankol/ubuntu-ocr:latest
      env:
        - name: CREDENTIALS
          valueFrom:
            secretKeyRef:
              name: db2-credentials
              key: credentials.txt
      imagePullPolicy: Always
      stdin: true
      tty: true
      command: ["/usr/bin/python3"]
      args: ["ocr_server.py"]
```

### 3.1. Testing Secrets

1. Create the Pod
   ```commandline
   kubectl apply -f ./kubernetes/kube-config.yml 
   ``` 
   Output:
   ```
   service/api-service unchanged
   pod/ubuntu-ocr configured
   ```

2. List Pods
   ```commandline
   kubectl get pods
   ```
   Output:
   ```
   NAME         READY   STATUS    RESTARTS   AGE
   ubuntu-ocr   1/1     Running   0          44s
   ```

3. Print Env Variables
   ```commandline
   kubectl exec ubuntu-ocr env
   ```
   Output: Lists out the env vars for the pod ubuntu-ocr

## Reference:
1. https://kubernetes.io/docs/concepts/configuration/secret/
2. https://www.youtube.com/watch?v=tZEKGNnvBzg
