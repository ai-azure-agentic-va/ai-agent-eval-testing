#!/bin/bash
# Deploy Agent Evaluation Web Interface to Azure Container Apps

set -e

# Configuration
APP_NAME="ai-agent-eval-testing"
RESOURCE_GROUP="rg-agent-eval"
LOCATION="eastus"
ACR_NAME="acragenteval"
IMAGE_NAME="agent-eval-web"
IMAGE_TAG="latest"

echo "🚀 Deploying Agent Evaluation Web Interface to Azure Container Apps"
echo "App Name: $APP_NAME"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
echo "Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Running 'az login'..."
    az login
fi

echo "✅ Azure CLI authenticated"
echo ""

# Create resource group if it doesn't exist
echo "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none 2>/dev/null || echo "Resource group already exists"

# Create Azure Container Registry if it doesn't exist
echo "Creating Azure Container Registry: $ACR_NAME"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true \
    --output none 2>/dev/null || echo "ACR already exists"

# Build and push Docker image to ACR
echo ""
echo "Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image $IMAGE_NAME:$IMAGE_TAG \
    --file Dockerfile \
    .

# Get ACR credentials
ACR_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

echo ""
echo "✅ Image pushed to: $ACR_SERVER/$IMAGE_NAME:$IMAGE_TAG"
echo ""

# Create Container Apps environment if it doesn't exist
ENVIRONMENT_NAME="env-agent-eval"
echo "Creating Container Apps environment: $ENVIRONMENT_NAME"
az containerapp env create \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output none 2>/dev/null || echo "Environment already exists"

# Deploy Container App
echo ""
echo "Deploying Container App: $APP_NAME"
az containerapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
    --registry-server $ACR_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --target-port 8501 \
    --ingress external \
    --cpu 1.0 \
    --memory 2Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --query properties.configuration.ingress.fqdn \
    --output tsv 2>/dev/null || \
az containerapp update \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$ACR_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
    --query properties.configuration.ingress.fqdn \
    --output tsv

# Get the application URL
APP_URL=$(az containerapp show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Application URL: https://$APP_URL"
echo ""
echo "To set environment variables (Azure OpenAI, Agent Endpoint):"
echo "  az containerapp update \\"
echo "    --name $APP_NAME \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --set-env-vars \\"
echo "      AZURE_OPENAI_ENDPOINT=<your-endpoint> \\"
echo "      AZURE_OPENAI_API_KEY=secretref:openai-key \\"
echo "      AGENT_ENDPOINT=<your-agent-endpoint>"
echo ""
echo "To add secrets:"
echo "  az containerapp secret set \\"
echo "    --name $APP_NAME \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --secrets openai-key=<your-key>"
echo ""
