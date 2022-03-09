FROM python:3
WORKDIR /usr/src/app
COPY . .

RUN pip install requests pandas influxdb

RUN pwd
RUN ls -l /usr/src/app/

CMD ["./weather-upload.py"]
ENTRYPOINT ["python3"]

