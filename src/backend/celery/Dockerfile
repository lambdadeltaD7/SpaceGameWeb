FROM python

WORKDIR /app

COPY ./requirements.txt ./
RUN pip install -r ./requirements.txt --no-cache-dir

COPY ./*.py ./

CMD ["celery", "-A", "tasks", "beat", "--loglevel=info"]