#!/bin/bash
# Complete deployment configuration generator

PLATFORM="${1:-docker}"
APP_NAME="${2:-fastapi-app}"
PORT="${3:-8000}"

python3 << EOF
import os
from pathlib import Path

platform = "$PLATFORM"
app_name = "$APP_NAME"
port = "$PORT"

if platform == "docker":
    # Generate Dockerfile
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE ''' + port + '''

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:''' + port + '''/health')" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "''' + port + '''"]
'''

    # Generate docker-compose.yml
    compose_content = '''version: '3.8'

services:
  app:
    build: .
    container_name: ''' + app_name + '''
    ports:
      - "''' + port + ''':''' + port + '''"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/''' + app_name + '''_db
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=\${SECRET_KEY:-change-this-in-production}
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app
    restart: unless-stopped
    networks:
      - app-network

  db:
    image: postgres:15-alpine
    container_name: ''' + app_name + '''_db
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: ''' + app_name + '''_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    container_name: ''' + app_name + '''_redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: ''' + app_name + '''_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
'''

    # Generate nginx.conf
    nginx_content = '''events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:''' + port + ''';
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /ws {
            proxy_pass http://app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
'''

    # Generate deployment script
    deploy_script = '''#!/bin/bash
set -e

echo "Deploying ''' + app_name + '''..."

# Build and start services
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Run migrations
docker-compose exec app alembic upgrade head

# Health check
if curl -f http://localhost:''' + port + '''/health; then
    echo "✓ Deployment successful!"
    docker-compose ps
else
    echo "✗ Deployment failed!"
    docker-compose logs app
    exit 1
fi
'''

    # Write files
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    with open("nginx.conf", "w") as f:
        f.write(nginx_content)
    
    with open("deploy.sh", "w") as f:
        f.write(deploy_script)
    
    os.chmod("deploy.sh", 0o755)
    
    print(f"✓ Docker deployment configuration created:")
    print(f"  - Dockerfile")
    print(f"  - docker-compose.yml")
    print(f"  - nginx.conf")
    print(f"  - deploy.sh")

elif platform == "kubernetes":
    # Generate Kubernetes manifests
    k8s_dir = Path("k8s")
    k8s_dir.mkdir(exist_ok=True)
    
    deployment_yaml = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: ''' + app_name + '''
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ''' + app_name + '''
  template:
    metadata:
      labels:
        app: ''' + app_name + '''
    spec:
      containers:
      - name: app
        image: ''' + app_name + ''':latest
        ports:
        - containerPort: ''' + port + '''
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
name: db-secret
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secret
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: ''' + port + '''
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: ''' + port + '''
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ''' + app_name + '''-service
spec:
  selector:
    app: ''' + app_name + '''
  ports:
  - port: 80
    targetPort: ''' + port + '''
  type: LoadBalancer
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:
  secret-key: change-this-secret-key
---
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  database-url: postgresql://user:pass@postgres:5432/''' + app_name + '''_db
'''
    
    with open(k8s_dir / "deployment.yaml", "w") as f:
        f.write(deployment_yaml)
    
    print(f"✓ Kubernetes deployment created:")
    print(f"  - k8s/deployment.yaml")

print(f"Platform: {platform}")
print(f"App Name: {app_name}")
print(f"Port: {port}")
EOF

if [ -n "$ARGUMENTS" ]; then
    echo "Additional deployment options: $ARGUMENTS"
fi
