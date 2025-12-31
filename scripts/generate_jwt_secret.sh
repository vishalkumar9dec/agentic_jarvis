#!/bin/bash
# Generate a secure JWT secret key
# Usage: ./scripts/generate_jwt_secret.sh

echo "Generating secure JWT secret key..."
echo ""

# Generate a 32-byte (256-bit) URL-safe secret
SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "Your JWT secret key:"
echo ""
echo "  $SECRET"
echo ""
echo "Add this to your .env file:"
echo ""
echo "  JWT_SECRET_KEY=$SECRET"
echo ""
echo "IMPORTANT: Keep this secret secure!"
echo "- Never commit it to version control"
echo "- Use different secrets for dev/staging/production"
echo "- Rotate secrets periodically for security"
echo ""
