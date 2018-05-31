FROM python:3
ADD . /brokerage
WORKDIR /brokerage
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 8000
