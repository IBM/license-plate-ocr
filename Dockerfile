FROM ubuntu:trusty
RUN apt-get update -y
RUN apt-get install -y curl python3-dev python3-numpy
# sudo apt install python3-numpy python3-scipy
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
ADD requirements.txt /root/
RUN pip install -r requirements.txt
