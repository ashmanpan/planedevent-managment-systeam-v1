# Kubernetes Deployment Guide

This directory contains Kubernetes deployment files for the Planned Event Management System (PEMS).

## Files Overview

- `secrets.yaml` - Contains all sensitive credentials (passwords, API keys, etc.)
- `backend-deployment.yaml` - Backend API deployment and service
- `frontend-deployment.yaml` - Frontend web application deployment and service

## Prerequisites

1. Kubernetes cluster is up and running
2. kubectl is configured to connect to your cluster
3. ECR registry access is configured
4. Docker images are built and pushed to ECR

## Setup ECR Registry Secret

Before deploying, create the ECR registry secret:

```bash
kubectl create secret docker-registry ecr-registry-secret \
  --docker-server=567097740753.dkr.ecr.ap-southeast-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region ap-southeast-1) \
  --namespace=pems
```

## Deployment Steps

### 1. Update Secrets

Edit `secrets.yaml` and update the following values:
- `DB_PASSWORD` - Change to a strong database password
- `SECRET_KEY` - Generate a strong random key for JWT
- `EXTERNAL_DEVICE_API_KEY` - Add your actual API key

### 2. Deploy in Order

```bash
# Create namespace and secrets
kubectl apply -f secrets.yaml

# Deploy backend
kubectl apply -f backend-deployment.yaml

# Deploy frontend
kubectl apply -f frontend-deployment.yaml
```

### 3. Verify Deployment

```bash
# Check if all pods are running
kubectl get pods -n pems

# Check services
kubectl get svc -n pems

# Check deployment status
kubectl get deployments -n pems
```

## Accessing the Application

### Frontend
```bash
# Get the NodePort for frontend
kubectl get svc pems-frontend-service -n pems

# Access via: http://<node-ip>:<node-port>
```

### Backend API
```bash
# Get the backend service details
kubectl get svc pems-backend-service -n pems

# For internal access: http://pems-backend-service.pems.svc.cluster.local:8000
```

## Scaling

To scale the deployments:

```bash
# Scale backend
kubectl scale deployment pems-backend --replicas=3 -n pems

# Scale frontend
kubectl scale deployment pems-frontend --replicas=2 -n pems
```

## Updating Images

After building new Docker images:

```bash
# Push new images to ECR
docker tag pems-backend:latest 567097740753.dkr.ecr.ap-southeast-1.amazonaws.com/apj/can-aaipe:backend-latest
docker push 567097740753.dkr.ecr.ap-southeast-1.amazonaws.com/apj/can-aaipe:backend-latest

docker tag pems-frontend:latest 567097740753.dkr.ecr.ap-southeast-1.amazonaws.com/apj/can-aaipe:frontend-latest
docker push 567097740753.dkr.ecr.ap-southeast-1.amazonaws.com/apj/can-aaipe:frontend-latest

# Restart deployments to pull new images
kubectl rollout restart deployment pems-backend -n pems
kubectl rollout restart deployment pems-frontend -n pems
```

## Viewing Logs

```bash
# Backend logs
kubectl logs -f deployment/pems-backend -n pems

# Frontend logs
kubectl logs -f deployment/pems-frontend -n pems

# Specific pod logs
kubectl logs <pod-name> -n pems
```

## Troubleshooting

### Check pod status
```bash
kubectl describe pod <pod-name> -n pems
```

### Check events
```bash
kubectl get events -n pems --sort-by='.lastTimestamp'
```

### Access pod shell
```bash
kubectl exec -it <pod-name> -n pems -- /bin/sh
```

### Verify secrets
```bash
kubectl get secrets -n pems
kubectl describe secret pems-secrets -n pems
```

## Cleanup

To remove all deployments:

```bash
kubectl delete namespace pems
```

Or delete individual resources:

```bash
kubectl delete -f frontend-deployment.yaml
kubectl delete -f backend-deployment.yaml
kubectl delete -f secrets.yaml
```

## Important Notes

1. The database is not included in these deployments - ensure your database is accessible from the cluster
2. Update the `DATABASE_URL` in `secrets.yaml` to point to your actual database
3. Make sure to update all placeholder values in `secrets.yaml` before deploying to production
4. Consider using a proper secrets management solution like AWS Secrets Manager or HashiCorp Vault for production
