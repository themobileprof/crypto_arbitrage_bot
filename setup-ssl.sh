#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOMAIN="ex.otomatiktech.com"

echo -e "${GREEN}🔐 SSL Certificate Setup for $DOMAIN${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}📦 Installing certbot...${NC}"
    apt update
    apt install -y certbot
fi

# Check if domain resolves
echo -e "${YELLOW}🌐 Checking domain resolution...${NC}"
if ! nslookup $DOMAIN > /dev/null 2>&1; then
    echo -e "${RED}❌ Domain $DOMAIN does not resolve!${NC}"
    echo "Please ensure your domain points to this server's IP address."
    exit 1
fi

# Stop nginx temporarily
echo -e "${YELLOW}⏸️  Stopping nginx temporarily...${NC}"
docker-compose --profile with-nginx stop nginx 2>/dev/null || true

# Run certbot
echo -e "${YELLOW}🔐 Obtaining SSL certificate...${NC}"
certbot certonly --standalone \
    -d $DOMAIN \
    --non-interactive \
    --agree-tos \
    --email admin@otomatiktech.com \
    --expand

# Start nginx again
echo -e "${YELLOW}▶️  Starting nginx...${NC}"
docker-compose --profile with-nginx up -d nginx

# Test SSL certificate
echo -e "${YELLOW}🧪 Testing SSL certificate...${NC}"
if curl -s -I https://$DOMAIN | grep -q "HTTP/2 200\|HTTP/1.1 200"; then
    echo -e "${GREEN}✅ SSL certificate is working correctly!${NC}"
else
    echo -e "${YELLOW}⚠️  SSL certificate may need time to propagate.${NC}"
fi

echo -e "${GREEN}✅ SSL setup completed!${NC}"
echo -e "${GREEN}🌐 Your dashboard is now available at: https://$DOMAIN${NC}"
echo ""
echo -e "${YELLOW}📋 SSL Management:${NC}"
echo "  Renew certificate: sudo certbot renew"
echo "  Check certificate: sudo certbot certificates"
echo "  Auto-renewal: sudo crontab -e (add: 0 12 * * * /usr/bin/certbot renew --quiet)" 