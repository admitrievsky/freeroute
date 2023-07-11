FROM ubuntu:22.04
ARG interface
ARG config
ARG username
ARG password
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install python3-pip openvpn nftables -y
RUN pip install poetry
EXPOSE 8080
RUN python3 service/src/installer.py ${interface} ${config} -u ${username} -p ${password}
CMD [ "python3", "service/src/main.py" ]