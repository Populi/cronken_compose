FROM alpine:3.18

RUN apk add python3 py3-pip git tzdata

RUN python3 -m pip install git+https://github.com/Populi/cronken.git

COPY cronken_server.py /cronken/

CMD ["/usr/bin/python3", "/cronken/cronken_server.py"]
