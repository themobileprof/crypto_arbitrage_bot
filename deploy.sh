#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOMAIN="ex.otomatiktech.com"

echo -e "${GREEN}🚀 Crypto Arbitrage Bot Deployment Script${NC}"
echo -e "${GREEN}Domain: ${DOMAIN}${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create a .env file with your API credentials:"
    cat << EOF
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
KUCOIN_API_KEY=your_kucoin_api_key
KUCOIN_API_SECRET=your_kucoin_api_secret
KUCOIN_API_PASSPHRASE=your_kucoin_api_passphrase
DASHBOARD_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
EOF
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p db logs

# Check if domain resolves to this server
echo -e "${YELLOW}🌐 Checking domain resolution...${NC}"
if ! nslookup $DOMAIN > /dev/null 2>&1; then
    echo -e "${RED}❌ Domain $DOMAIN does not resolve!${NC}"
    echo "Please ensure your domain points to this server's IP address."
    exit 1
fi

# Create dashboard user
echo -e "${YELLOW}👤 Creating dashboard user...${NC}"
read -p "Enter dashboard username: " username
read -s -p "Enter dashboard password: " password
echo

# Build and start the application (without nginx first)
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker compose build

echo -e "${YELLOW}🚀 Starting application...${NC}"
docker compose up -d crypto-arbitrage-scheduler crypto-arbitrage-web

# Wait for the container to be ready
echo -e "${YELLOW}⏳ Waiting for application to start...${NC}"
sleep 10

# Create dashboard user
echo -e "${YELLOW}👤 Creating dashboard user...${NC}"
docker compose exec crypto-arbitrage-web python src/main.py --create-user "$username" "$password"

# Start nginx with HTTP only
echo -e "${YELLOW}🌐 Starting nginx with HTTP...${NC}"
docker compose --profile with-nginx up -d nginx

# Check if certbot is available
if command -v certbot &> /dev/null; then
    echo -e "${YELLOW}🔐 Setting up SSL certificate with Let's Encrypt...${NC}"
    echo "This will temporarily stop nginx to verify domain ownership..."
    
    # Stop nginx temporarily for certbot
    docker compose --profile with-nginx stop nginx
    
    # Run certbot
    sudo certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email admin@otomatiktech.com
    
    # Start nginx again
    docker compose --profile with-nginx up -d nginx
    
    echo -e "${GREEN}✅ SSL certificate obtained successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Certbot not found. SSL certificate not configured.${NC}"
    echo "To install certbot: sudo apt install certbot"
    echo "Then run: sudo certbot --nginx -d $DOMAIN"
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Dashboard available at: https://$DOMAIN${NC}"
echo -e "${GREEN}📊 Login with username: $username${NC}"
echo ""
echo -e "${YELLOW}📋 Useful commands:${NC}"
echo "  View logs: docker compose logs -f"
echo "  Stop services: docker compose down"
echo "  Restart services: docker compose restart"
echo "  Update application: ./deploy.sh"
echo "  Renew SSL: sudo certbot renew"
echo ""
echo -e "${YELLOW}🔒 Security notes:${NC}"
echo "  - SSL certificate will auto-renew"
echo "  - Use strong passwords for dashboard access"
echo "  - Monitor logs for suspicious activity"
echo "  - Regular backups of the database directory" 