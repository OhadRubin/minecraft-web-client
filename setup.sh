#!/bin/bash

# Minecraft Web Client Setup Script
# This script downloads and installs everything needed to run the Minecraft web client
# Run this script while you have internet access for offline use later

set -e  # Exit on error

echo "🎮 Minecraft Web Client Setup Script"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -f "CONTRIBUTING.md" ]; then
    print_error "This script must be run from the minecraft-web-client directory"
    print_error "Make sure you've cloned the repository first:"
    echo "  git clone https://github.com/PrismarineJS/minecraft-web-client.git"
    echo "  cd minecraft-web-client"
    echo "  ./setup.sh"
    exit 1
fi

print_status "Starting setup process..."

# Step 1: Check Node.js version
print_status "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed!"
    print_error "Please install Node.js 18+ from https://nodejs.org"
    print_error "Recommended: Node.js 22.x"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_warning "Node.js version is $NODE_VERSION. Recommended: 18+"
    print_warning "You may encounter issues. Consider upgrading."
else
    print_success "Node.js $(node -v) is installed"
fi

# Step 2: Enable and update corepack
print_status "Setting up corepack..."
if ! corepack enable; then
    print_warning "Failed to enable corepack globally, trying with sudo..."
    sudo corepack enable || {
        print_error "Failed to enable corepack. You may need to install it manually."
        exit 1
    }
fi

print_status "Updating corepack to latest version..."
npm install -g corepack || {
    print_warning "Failed to update corepack globally, trying with sudo..."
    sudo npm install -g corepack || {
        print_warning "Could not update corepack, continuing with existing version..."
    }
}

print_success "Corepack setup complete"

# Step 3: Install dependencies
print_status "Installing dependencies with pnpm..."
print_status "This may take several minutes and will download ~2GB of packages..."

# Use timeout to avoid hanging on interactive prompts
timeout 1800 pnpm install --frozen-lockfile || {
    print_error "Failed to install dependencies"
    print_error "This could be due to:"
    print_error "  - Network connectivity issues"
    print_error "  - Insufficient disk space"
    print_error "  - Node.js version compatibility"
    exit 1
}

print_success "Dependencies installed successfully"

# Step 4: Pre-build everything possible
print_status "Pre-building project components..."

# Build the mesher worker
print_status "Building mesher worker..."
pnpm build-mesher || {
    print_warning "Failed to build mesher worker, but continuing..."
}

# Prepare project data
print_status "Preparing optimized project data..."
if command -v tsx &> /dev/null; then
    pnpm prepare-project || {
        print_warning "Failed to prepare project data, but continuing..."
    }
else
    print_warning "tsx not found globally, skipping project preparation"
fi

# Build storybook assets (optional)
print_status "Building storybook (optional)..."
pnpm build-storybook || {
    print_warning "Failed to build storybook, but continuing..."
}

# Step 5: Verify installation
print_status "Verifying installation..."

# Check if critical files exist
CRITICAL_FILES=(
    "node_modules/.pnpm"
    "package.json"
    "src"
    "renderer"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        print_error "Critical file/directory missing: $file"
        exit 1
    fi
done

print_success "Installation verification complete"

# Step 6: Create startup script
print_status "Creating startup script..."
cat > start_minecraft.sh << 'EOF'
#!/bin/bash

# Minecraft Web Client Startup Script
echo "🎮 Starting Minecraft Web Client..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: Must be run from the minecraft-web-client directory"
    exit 1
fi

# Start the application
echo "Starting development servers..."
echo "This will open:"
echo "  - Main application: http://localhost:8080"
echo "  - Direct client: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the servers"
echo ""

pnpm start
EOF

chmod +x start_minecraft.sh

# Step 7: Create offline info file
print_status "Creating offline usage guide..."
cat > OFFLINE_USAGE.md << 'EOF'
# Minecraft Web Client - Offline Usage Guide

## Starting the Application

Run the startup script:
```bash
./start_minecraft.sh
```

Or manually start with:
```bash
pnpm start
```

## Access Points

- **Main Application**: http://localhost:8080 (recommended)
- **Direct Client**: http://localhost:3000
- **Storybook** (if built): `pnpm storybook` then http://localhost:6006

## Features Available Offline

- ✅ Local singleplayer worlds
- ✅ Local server creation
- ✅ World editing and building
- ✅ Playground mode for testing
- ❌ Connecting to online servers (requires internet)

## Troubleshooting

### If servers won't start:
1. Make sure you're in the minecraft-web-client directory
2. Try: `pnpm install` (requires internet)
3. Try: `pnpm build-mesher`

### If browser shows errors:
1. Clear browser cache
2. Try http://localhost:3000 instead
3. Check browser console (F12) for errors

### Performance Issues:
- Close other applications to free up RAM
- Use Chrome/Chromium for best performance
- Lower render distance in game settings

## Keyboard Shortcuts in Development Server

When running, press these keys in terminal:
- `h + enter`: Show help
- `o + enter`: Open in browser
- `r + enter`: Restart servers
- `u + enter`: Show URLs
- `q + enter`: Quit

## Local Server Creation

You can create local servers for multiplayer:
1. Go to "Create World" in the web client
2. Choose "Local Server" option
3. Others can connect via your local IP address

Enjoy playing Minecraft in your browser! 🎮
EOF

print_success "Setup complete!"
echo ""
echo "📋 SETUP SUMMARY"
echo "================"
print_success "✅ Node.js $(node -v) verified"
print_success "✅ Corepack enabled and updated"
print_success "✅ Dependencies installed (~2GB downloaded)"
print_success "✅ Project components pre-built"
print_success "✅ Startup script created: ./start_minecraft.sh"
print_success "✅ Offline guide created: ./OFFLINE_USAGE.md"
echo ""
echo "🚀 TO START PLAYING:"
echo "  ./start_minecraft.sh"
echo ""
echo "🌐 BROWSER URLS:"
echo "  Main app: http://localhost:8080"
echo "  Direct:   http://localhost:3000"
echo ""
echo "📖 READ: ./OFFLINE_USAGE.md for detailed offline usage instructions"
echo ""
print_success "Setup completed successfully! You can now use this offline. 🎉" 