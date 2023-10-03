FROM python:3.9
WORKDIR /code
COPY . .
RUN pip install -r requirements.txt --no-cache-dir
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]