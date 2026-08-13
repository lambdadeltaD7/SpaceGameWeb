FROM python:alpine

WORKDIR /app

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir endpoints
COPY ./endpoints/*.py ./endpoints/
COPY ./*.py ./

CMD python3 -m uvicorn --host 0.0.0.0 --port 8080 main:app