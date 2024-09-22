FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod a+x docker_run.sh

EXPOSE 8000
CMD ["bash", "-c", "/app/docker_run.sh"]
#CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]