FROM python:3.7-slim

# config app
ENV APP_HOME="/app" \
  APP_PATH="/app/server"

# install packages & config docker
RUN pip install matplotlib numpy selenium \
  opencv-python undetected_chromedriver==3.0.3

RUN apt-get update && \
  apt-get -y install wget chromium chromium-driver && \
  apt-get -y autoremove && \
  apt-get clean

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
  echo "Asia/Shanghai" > /etc/timezone

COPY ./* $APP_PATH/

WORKDIR ${APP_PATH}
CMD ["/usr/local/bin/python", "/app/server/main.py"]
