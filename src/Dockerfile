FROM python:3.7
LABEL maintainer "Chiemi Kato <chiemickato@gmail.com>"
WORKDIR /code
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY ./ ./
EXPOSE 8050
CMD ["python", "./app.py"]