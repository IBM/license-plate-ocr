FROM ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y curl python3-dev python-numpy build-essential #python-scipy
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.6 get-pip.py
RUN apt-get install python3-opencv -y
RUN apt-get install tesseract-ocr -y
ADD requirements.txt /root/
RUN pip3.6 install -r /root/requirements.txt
ADD ocr_server_tess4.py /
ADD db2_script.py /
