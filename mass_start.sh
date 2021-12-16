docker-compose -f ./docker/docker-compose.yml up --build  -d --scale agent=$1
echo "You can copy everything below this line and save as CSV file to use bulk registration!"
echo "ID;PATH"
docker stats --no-stream --format "{{.Container}};"