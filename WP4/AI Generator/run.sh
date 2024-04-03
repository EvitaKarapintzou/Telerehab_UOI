sudo docker rm ai_generator_api
sudo docker build -t ai_generator_api:v1 .
sudo docker run -it --name ai_generator_api -e URL=http://0.0.0.0:8080 -p 8080:8080 ai_generator_api:v1

