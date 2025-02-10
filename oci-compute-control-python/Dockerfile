FROM fnproject/python:3.9
WORKDIR /function
ADD requirements.txt /function/

RUN true \
	&& pip3 install --target /python/ --no-cache --no-cache-dir -r requirements.txt \ 
	&& rm -fr ~/.cache/pip /tmp* requirements.txt func.yaml Dockerfile .venv \ 
	&& chmod -R o+r /python

# Install ping (iputils)
# microdnf upgrade --refresh --best --nodocs --noplugins --setopt=install_weak_deps=0
# RUN microdnf install -y iputils && microdnf clean all
RUN true \
    # && microdnf update --nodocs \
    # && microdnf upgrade --refresh --best --nodocs --noplugins --setopt=install_weak_deps=0 \ 
	&& microdnf install -y iputils --setopt=install_weak_deps=0 \
	&& microdnf clean all \
	&& groupadd --gid 1000 fn \
    && adduser --uid 1000 --gid fn fn

ADD . /function/
RUN rm -fr /function/.pip_cache

RUN chmod -R o+r /function
# RUN chmod o+rx /usr/bin/ping
RUN chmod u+s /usr/bin/ping
RUN setcap 'cap_net_raw+ep' /usr/bin/ping
RUN chmod +s /usr/bin/ping

ENV PYTHONPATH=/function:/python

ENTRYPOINT ["/python/bin/fdk", "/function/func.py", "handler"]
# ENTRYPOINT ["/bin/bash"]
