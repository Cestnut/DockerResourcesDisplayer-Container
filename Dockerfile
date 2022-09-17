FROM python:3.8-slim-buster
WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN mkdir resource_logs

COPY . .

CMD [ "python3", "script.py"]
EXPOSE 5000/tcp
