FROM python:3.8

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install python-lxml python3-peewee -y

WORKDIR /code

COPY requirements.txt .
COPY ./src .

RUN pip install --user -r requirements.txt

CMD [ "python", "main.py" ]