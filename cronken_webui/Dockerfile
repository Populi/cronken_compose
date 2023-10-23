FROM alpine:3.18

RUN apk add python3 py3-pip git tzdata

RUN mkdir /cronken_webui

RUN git clone https://github.com/Populi/cronken_webui.git /cronken_webui

RUN python3 -m pip install /cronken_webui

CMD ["/usr/bin/python3", "/cronken_webui/cronken_webui.py"]
