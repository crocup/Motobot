FROM python:3.6
RUN pip3 install pipenv
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install python-lxml python3-peewee python-sqlite -y
COPY /src ./
RUN pip install -r requirements.txt
CMD [ "python", "./main.py" ]