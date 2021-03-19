# set base image (host OS)
FROM python:3.8

# set the working directory in the container
WORKDIR /code

# copy dependencies into working directory
COPY requirements.txt .

# install dependencies
RUN pip3 install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY src/ .

# command to run on container start
CMD ["python3", "./tazer.py"]