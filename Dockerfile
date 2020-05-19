FROM arm32v7/ubuntu:latest

LABEL maintainer="Kevin Hill"

RUN apt-get update -y
RUN apt-get install -y --no-install-recommends python3 python3-virtualenv python3-pip

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install dependencies:
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Run the application:
ENV FLASK_APP=sysinfo.py
COPY sysinfo.py .
CMD ["flask", "run", "--host", "0.0.0.0"]
