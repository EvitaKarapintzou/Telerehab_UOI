sudo docker rm ai-generator-api
sudo docker build -t flaskapi:v1 .
sudo docker run -it --name ai-generator-api -p 8080:8080 flaskapi:v1
