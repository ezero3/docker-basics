FROM python:3.12-slim 
# node:20 , ubuntu

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . . 

# there is an alternative that is ADD , that allows also to 
# pull files from a URL like a github repository

EXPOSE 5000
CMD ["python", "app.py"]