#Author: Fatih Keles <fatih.k.keles@oracle.com>
FROM fnproject/python:3.9-dev as build-stage
WORKDIR /function
ADD requirements.txt /function/

RUN pip3 install --target /python/  --no-cache --no-cache-dir -r requirements.txt &&\
	rm -fr ~/.cache/pip /tmp* requirements.txt func.yaml Dockerfile .venv &&\
	chmod -R o+r /python
ADD . /function/
RUN rm -fr /function/.pip_cache

FROM fnproject/python:3.9
RUN microdnf install -y oracle-epel-release-el8 &&\
    dnf install -y opencv-core opencv-contrib &&\
    pip3 install --target /python/ --no-cache opencv-python &&\
    microdnf remove oracle-epel-release-el8 &&\
    microdnf clean all
WORKDIR /function
COPY --from=build-stage /python /python
COPY --from=build-stage /function /function
RUN chmod -R o+r /function
ENV PYTHONPATH=/function:/python
RUN python3 -c "import cv2; print(cv2.__version__);"
ENTRYPOINT ["/python/bin/fdk", "/function/func.py", "handler"]

#
#microdnf install -y oracle-epel-release-el8
#dnf install -y opencv-core opencv-contrib
#pip3 install --target /python/ --no-cache opencv-python

#python3 -c "import cv2; print(cv2.__version__);"
#/python/cv2/data/haarcascade_frontalface_default.xml