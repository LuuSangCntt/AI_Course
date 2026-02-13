docker build -t mcp-mysql-server .

docker run -d  --name mcp-mysql-sql  -p 8001:8000  -e DB_HOST=host.docker.internal  mcp-mysql-server


docker rm mcp-mysql-sql
