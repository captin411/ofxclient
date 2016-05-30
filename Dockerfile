FROM python:2.7-onbuild
MAINTAINER David Bartle <captindave@gmail.com>

RUN mkdir -p /root/.local/share/python_keyring
RUN mkdir -p /export

COPY keyringrc.cfg /root/.local/share/python_keyring

RUN python setup.py install

VOLUME /export
VOLUME /root/.local/share/python_keyring

# so that ofxclient will download to the shared volume by default
WORKDIR /export

ENTRYPOINT ["ofxclient", "-c", "/export/ofxconfig.ini"]
