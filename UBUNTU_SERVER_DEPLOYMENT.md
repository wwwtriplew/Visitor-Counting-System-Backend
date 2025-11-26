# Ubuntu Server 24.04 Production Deployment Guide
## Complete Step-by-Step Reference for HTTP Ingestion Server

---

## 📋 Table of Contents

1. [Server Information & Prerequisites](#server-information--prerequisites)
2. [Initial Server Setup](#initial-server-setup)
3. [Network Configuration Deep Dive](#network-configuration-deep-dive)
4. [System Dependencies Installation](#system-dependencies-installation)
5. [Python Environment Setup](#python-environment-setup)
6. [Application Configuration](#application-configuration)
7. [Testing & Validation](#testing--validation)
8. [Production Deployment Options](#production-deployment-options)
9. [Security Hardening](#security-hardening)
10. [Monitoring & Logging](#monitoring--logging)
11. [Camera Integration](#camera-integration)
12. [Performance Tuning](#performance-tuning)
13. [Backup & Disaster Recovery](#backup--disaster-recovery)
14. [Troubleshooting Guide](#troubleshooting-guide)
15. [Maintenance Operations](#maintenance-operations)

---

## Server Information & Prerequisites

**Received Credentials:**
- **Fixed LAN IP**: [To be filled in] - e.g., `192.168.1.100`
- **WiFi SSID**: [To be filled in] - e.g., `Building-WiFi-2.4GHz`
- **WiFi Password**: [To be filled in]
- **Server Hostname**: [Optional] - e.g., `visitor-server`
- **Admin Username**: [Default: first user created during Ubuntu install]

**Hardware Requirements:**

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| CPU | 2 cores (2.0 GHz) | 4+ cores (2.5 GHz+) | More cores = more concurrent cameras |
| RAM | 4 GB | 8+ GB | YOLO model uses ~2GB when loaded |
| Storage | 20 GB | 50+ GB SSD | For OS, logs, and future growth |
| Network | 10 Mbps LAN | 100 Mbps LAN | Gigabit preferred for many cameras |

**Software Versions:**
- **OS**: Ubuntu Server 24.04 LTS (headless, no GUI)
- **Python**: 3.11 or 3.12 (NOT 3.13 - compatibility issues)
- **OpenCV**: opencv-python-headless 4.8+ (headless is critical!)

**Network Topology:**
```
Internet Router (192.168.1.1)
    │
    ├─── WiFi AP (2.4/5 GHz)
    │       ├─── Camera 1 (192.168.1.101)
    │       ├─── Camera 2 (192.168.1.102)
    │       └─── Camera N (192.168.1.10N)
    │
    └─── Ubuntu Server (192.168.1.100) ← Fixed IP
              │
              └─── Serves HTTP on port 8000
```

---

## Initial Server Setup

### Step 1: Physical Server Access

**If you have physical access:**
```bash
# Connect monitor and keyboard
# Login with credentials provided during Ubuntu installation
# Username: <your-admin-user>
# Password: <set-during-install>
```

**First commands after login:**
```bash
# Check current IP address
ip addr show

# You should see your fixed IP (e.g., 192.168.1.100) on interface wlan0 or eth0
# Example output:
#   wlan0: inet 192.168.1.100/24

# Test internet connectivity
ping -c 4 8.8.8.8
ping -c 4 google.com

# If no internet, see Network Configuration section below
```

### Step 2: Enable SSH for Remote Access

```bash
# Install OpenSSH server (if not already installed)
sudo apt update
sudo apt install -y openssh-server

# Enable and start SSH service
sudo systemctl enable ssh
sudo systemctl start ssh

# Check SSH is running
sudo systemctl status ssh

# Verify SSH is listening on port 22
sudo ss -tulnp | grep :22

# Allow SSH through firewall
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status
```

**Test SSH from your laptop:**
```bash
# From another device on same LAN
ssh username@192.168.1.100

# If connection refused, check:
# 1. Server firewall: sudo ufw status
# 2. SSH running: sudo systemctl status ssh
# 3. IP address: ip addr show
```

**SSH Security Tips:**
```bash
# Disable root login (recommended)
sudo nano /etc/ssh/sshd_config
# Change: PermitRootLogin no
# Change: PasswordAuthentication yes (for now, use keys later)

# Restart SSH
sudo systemctl restart ssh

# Optional: Setup SSH keys for passwordless login
# On your laptop:
ssh-keygen -t ed25519 -C "your-email@example.com"
ssh-copy-id username@192.168.1.100
```

---

## Network Configuration Deep Dive

### Understanding Your Network Setup

**Check current network configuration:**
```bash
# List all network interfaces
ip link show

# Show IP addresses
ip addr show

# Show routing table
ip route show

# Show DNS configuration
cat /etc/resolv.conf

# Test gateway connectivity
ping -c 4 $(ip route | grep default | awk '{print $3}')
```

### WiFi Configuration (If Using WiFi)

**Method 1: Using netplan (Ubuntu 24.04 default)**

```bash
# List netplan configurations
ls -la /etc/netplan/

# Edit netplan config (usually 00-installer-config.yaml or 50-cloud-init.yaml)
sudo nano /etc/netplan/00-installer-config.yaml
```

**Example netplan configuration for WiFi with fixed IP:**
```yaml
network:
  version: 2
  renderer: networkd
  wifis:
    wlan0:
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
      access-points:
        "Your-WiFi-SSID":
          password: "your-wifi-password"
```

**Apply configuration:**
```bash
# Test configuration (won't apply yet)
sudo netplan try

# If successful, apply permanently
sudo netplan apply

# Check status
ip addr show wlan0
ping -c 4 google.com
```

### Ethernet Configuration (If Using Wired)

**Example netplan for fixed IP on ethernet:**
```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:  # or enp0s3, check with 'ip link show'
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

### Network Troubleshooting

**Problem: No internet connectivity**
```bash
# Step 1: Check physical link
ip link show
# Look for "state UP" on your interface

# Step 2: Check IP address
ip addr show
# Should show your fixed IP (e.g., 192.168.1.100/24)

# Step 3: Check gateway
ip route show
# Should show: default via 192.168.1.1 dev wlan0

# Step 4: Ping gateway
ping -c 4 192.168.1.1
# If fails, network configuration is wrong

# Step 5: Ping external IP
ping -c 4 8.8.8.8
# If fails but gateway works, check routes

# Step 6: Test DNS
ping -c 4 google.com
# If fails but 8.8.8.8 works, DNS issue

# Fix DNS
sudo nano /etc/resolv.conf
# Add:
nameserver 8.8.8.8
nameserver 8.8.4.4
```

**Problem: IP address conflicts**
```bash
# Check for duplicate IPs on network
sudo apt install -y arping
sudo arping -I wlan0 192.168.1.100

# If duplicate found, change your fixed IP in netplan
sudo nano /etc/netplan/00-installer-config.yaml
# Change to: 192.168.1.101 or another free IP
sudo netplan apply
```

**Setting hostname (optional but recommended):**
```bash
# Set hostname
sudo hostnamectl set-hostname visitor-server

# Update /etc/hosts
sudo nano /etc/hosts
# Add: 127.0.1.1  visitor-server

# Verify
hostnamectl
```

---

## System Dependencies Installation

### Step 1: System Update & Essential Tools

```bash
# Update package lists
sudo apt update

# Upgrade all packages (this may take 10-30 minutes)
sudo apt upgrade -y

# Install essential build tools
sudo apt install -y \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    ufw

# Verify installations
which git curl wget
git --version
```

**Understanding package installations:**
- `build-essential`: Compiler and build tools (for Python packages with C extensions)
- `curl/wget`: Download tools (for testing API endpoints)
- `git`: Version control (for cloning repository)
- `vim/nano`: Text editors (for config files)
- `htop`: Process monitor (for troubleshooting)
- `net-tools`: Network utilities (netstat, ifconfig)
- `ufw`: Firewall (for security)

### Step 2: Python Installation

```bash
# Check Python version (Ubuntu 24.04 includes Python 3.12)
python3 --version
# Should output: Python 3.12.x

# If Python is older than 3.11, install from deadsnakes PPA:
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Install pip
sudo apt install -y python3-pip

# Verify pip
pip3 --version

# Upgrade pip to latest
python3 -m pip install --upgrade pip
```

### Step 3: OpenCV System Dependencies (Critical!)

**⚠️ Ubuntu Server is HEADLESS - no GUI, no X11, no display**

This means we MUST use `opencv-python-headless` (NOT `opencv-python`).

```bash
# Install OpenCV system dependencies
sudo apt install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libgtk2.0-dev \
    pkg-config

# These libraries provide:
# - libglib2.0-0: Core GLib library
# - libsm6, libxext6, libxrender-dev: X11 libraries (for headless image ops)
# - libgomp1: OpenMP (parallel processing)
# - libgl1-mesa-glx: OpenGL (for some CV operations)
```

**Why headless matters:**
```python
# opencv-python tries to use:
import cv2
cv2.imshow()  # ❌ FAILS on headless server (no display)

# opencv-python-headless:
import cv2
cv2.imread()   # ✅ Works (file operations)
cv2.imencode() # ✅ Works (image encoding)
# No GUI functions, perfect for servers
```

### Step 4: Additional Utilities

```bash
# Install monitoring tools
sudo apt install -y \
    iotop \      # Disk I/O monitor
    iftop \      # Network monitor
    sysstat \    # System statistics
    dstat        # Resource statistics

# Install screen for background processes
sudo apt install -y screen tmux

# Install log management
sudo apt install -y logrotate rsyslog
```

---

## Python Environment Setup

### Understanding Virtual Environments

**Why use virtual environments?**
- Isolates project dependencies from system Python
- Prevents conflicts between different projects
- Makes deployment reproducible
- Allows different Python versions per project

**Virtual environment workflow:**
```
System Python (/usr/bin/python3)
    └── venv/ (isolated environment)
        └── site-packages/ (project-specific packages)
```

### Step 1: Create Project Directory Structure

```bash
# Create organized directory structure
mkdir -p ~/visitor-counting
cd ~/visitor-counting

# Recommended structure:
# ~/visitor-counting/
#   ├── Visitor-Counting-System-Backend/  (git repo)
#   ├── logs/                              (application logs)
#   ├── backups/                           (configuration backups)
#   └── scripts/                           (maintenance scripts)

mkdir -p logs backups scripts

# Verify structure
ls -la ~/visitor-counting/
```

### Step 2: Clone Repository

```bash
cd ~/visitor-counting

# Clone from GitHub
git clone https://github.com/wwwtriplew/Visitor-Counting-System-Backend.git

# Enter repository
cd Visitor-Counting-System-Backend

# Check current branch
git branch
git status

# View repository structure
tree -L 2  # or: ls -R
```

**Repository structure you should see:**
```
Visitor-Counting-System-Backend/
├── backend/              # Processing pipeline
│   ├── config.py
│   ├── process_images.py
│   └── utils/
├── server/               # HTTP ingestion server
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
├── Test/                 # Test suite
├── testing_images/       # Sample images
├── requirements.txt      # Main dependencies
└── .env.example          # Environment template
```

### Step 3: Create Virtual Environment

```bash
# Ensure you're in repository directory
cd ~/visitor-counting/Visitor-Counting-System-Backend

# Create virtual environment with Python 3.12
python3 -m venv venv

# This creates:
# venv/
#   ├── bin/           # Executables (python, pip, gunicorn)
#   ├── lib/           # Python packages
#   ├── include/       # C headers
#   └── pyvenv.cfg     # Configuration

# Verify venv was created
ls -la venv/
```

### Step 4: Activate Virtual Environment

```bash
# Activate venv (you'll do this every time you work on the project)
source venv/bin/activate

# Your prompt will change to show (venv):
# (venv) username@visitor-server:~/visitor-counting/Visitor-Counting-System-Backend$

# Verify Python is from venv
which python3
# Output: /home/username/visitor-counting/Visitor-Counting-System-Backend/venv/bin/python3

which pip
# Output: /home/username/visitor-counting/Visitor-Counting-System-Backend/venv/bin/pip

# Check Python version
python3 --version
```

**To deactivate venv later:**
```bash
deactivate
# Prompt returns to normal
```

### Step 5: Upgrade pip and Install Build Tools

```bash
# Make sure venv is activated!
source venv/bin/activate

# Upgrade pip to latest version
pip install --upgrade pip

# Install setuptools and wheel (for building packages)
pip install --upgrade setuptools wheel

# Verify pip version
pip --version
# Should show: pip 24.x or higher
```

### Step 6: Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# This installs:
# - flask (web framework)
# - gunicorn (WSGI server)
# - ultralytics (YOLO v8)
# - opencv-python-headless (image processing)
# - supabase (database client)
# - python-dotenv (environment variables)
# - numpy, pillow, torch, etc. (dependencies)

# Installation will take 5-15 minutes depending on internet speed
# Watch for any errors during installation
```

**Common installation issues:**

**Issue 1: pip install fails with "externally managed environment"**
```bash
# Solution: Use virtual environment (you should already be in one)
# If you see this error, you're not in venv. Activate it:
source venv/bin/activate
```

**Issue 2: Torch installation is slow**
```bash
# PyTorch is large (>1GB). To speed up, use pre-built wheels:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

**Issue 3: opencv-python installed instead of headless**
```bash
# Check what's installed
pip list | grep opencv

# If you see opencv-python (not headless), uninstall it:
pip uninstall opencv-python -y
pip install opencv-python-headless
```

### Step 7: Verify Installation

```bash
# Test all critical imports
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")

import cv2
print(f"✓ OpenCV: {cv2.__version__}")

import flask
print(f"✓ Flask: {flask.__version__}")

import ultralytics
print(f"✓ Ultralytics: {ultralytics.__version__}")

from supabase import create_client
print(f"✓ Supabase: OK")

import numpy as np
print(f"✓ NumPy: {np.__version__}")

import PIL
print(f"✓ Pillow: {PIL.__version__}")

print("\n✅ All imports successful!")
EOF
```

**Expected output:**
```
Python: 3.12.x
✓ OpenCV: 4.8.x
✓ Flask: 3.1.x
✓ Ultralytics: 8.3.x
✓ Supabase: OK
✓ NumPy: 1.26.x
✓ Pillow: 10.x.x

✅ All imports successful!
```

### Step 8: List Installed Packages

```bash
# See all installed packages with versions
pip list

# Save to file for reference
pip freeze > installed_packages.txt

# Check package sizes (useful for troubleshooting)
du -sh venv/
# Typical size: 2-4 GB (PyTorch and YOLO are large)
```

---

## Application Configuration

### Understanding Environment Variables

**Why .env files?**
- Keeps secrets out of source code (never commit credentials to Git!)
- Easy to change configuration without code changes
- Different configs for dev/staging/production
- Secure: file permissions can restrict access

**Configuration hierarchy:**
```
1. System environment variables (highest priority)
2. .env file (loaded by python-dotenv)
3. Default values in code (fallback)
```

### Step 1: Create .env File

```bash
# Navigate to repository root
cd ~/visitor-counting/Visitor-Counting-System-Backend

# Check if .env.example exists
ls -la .env.example

# Copy template to .env
cp .env.example .env

# Or create from scratch if template doesn't exist
nano .env
```

### Step 2: Configure Environment Variables

**Complete .env configuration:**
```bash
# ============================================
# SUPABASE CONFIGURATION
# ============================================
SUPABASE_URL=https://rgkkadtaiivcuuvekwdo.supabase.co
SUPABASE_SERVICE_KEY=your-actual-service-role-key-here
TABLE_NAME=detections

# Important: Use SERVICE ROLE key, not ANON key!
# Get from: Supabase Dashboard → Settings → API → service_role key

# ============================================
# SERVER CONFIGURATION
# ============================================
INGESTION_API_KEY=Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# SERVER_HOST=0.0.0.0 means listen on ALL network interfaces
# This allows cameras on LAN to connect
# If you set 127.0.0.1, only localhost can connect!

# ============================================
# YOLO MODEL CONFIGURATION
# ============================================
YOLO_MODEL_PATH=yolov8n.pt
CONFIDENCE_THRESHOLD=0.5
IOU_THRESHOLD=0.45

# yolov8n.pt will be auto-downloaded on first run if missing
# Confidence: 0.5 = 50% minimum confidence for person detection
# IOU: Intersection over Union for non-max suppression

# ============================================
# PROCESSING CONFIGURATION
# ============================================
MAX_IMAGE_SIZE_MB=10
IMAGE_QUALITY=85

# Max image size before rejection (prevents DoS)
# Image quality: 85 is good balance (range 0-100)

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOG_LEVEL=INFO
LOG_FILE=/home/username/visitor-counting/logs/server.log

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Change username to your actual username!

# ============================================
# PERFORMANCE TUNING
# ============================================
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
GUNICORN_WORKER_CLASS=sync

# Workers: 2-4 x CPU cores (4 cores = 8-16 workers)
# Timeout: Max seconds per request (YOLO can be slow)
# Worker class: sync (default), gevent, or eventlet
```

### Step 3: Secure .env File

```bash
# Set restrictive permissions (owner read/write only)
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (only owner can read/write)

# NEVER commit .env to Git!
# Check .gitignore includes .env
cat .gitignore | grep .env

# If .env is not ignored, add it:
echo ".env" >> .gitignore
```

### Step 4: Get Supabase Service Key

**Method 1: Supabase Dashboard**
```
1. Go to https://supabase.com/dashboard
2. Select your project (rgkkadtaiivcuuvekwdo)
3. Click "Settings" (gear icon) in left sidebar
4. Click "API" under Project Settings
5. Under "Project API keys":
   - anon/public key: For frontend (limited permissions)
   - service_role key: For backend (full permissions) ← Use this!
6. Copy service_role key
7. Paste into .env: SUPABASE_SERVICE_KEY=eyJ...
```

**Method 2: Verify existing key**
```bash
# Test Supabase connection with Python
python3 << 'EOF'
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')

print(f"URL: {url}")
print(f"Key: {key[:20]}...")  # Print first 20 chars

try:
    client = create_client(url, key)
    # Test query
    result = client.table('detections').select('*').limit(1).execute()
    print("✅ Supabase connection successful!")
    print(f"Table 'detections' accessible: {len(result.data) >= 0}")
except Exception as e:
    print(f"❌ Supabase error: {e}")
EOF
```

### Step 5: Generate Secure API Key

The INGESTION_API_KEY authenticates cameras. **Keep this secret!**

**Generate a new random key (optional):**
```bash
# Method 1: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Using OpenSSL
openssl rand -base64 32

# Method 3: Using /dev/urandom
head -c 32 /dev/urandom | base64

# Copy the generated key and update .env:
# INGESTION_API_KEY=your-new-random-key
```

**Or use the provided key:**
```
INGESTION_API_KEY=Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI
```

### Step 6: Validate Configuration

```bash
# Test configuration loading
python3 << 'EOF'
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Check all required variables
required_vars = [
    'SUPABASE_URL',
    'SUPABASE_SERVICE_KEY',
    'TABLE_NAME',
    'INGESTION_API_KEY',
    'SERVER_HOST',
    'SERVER_PORT',
]

missing = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'KEY' in var:
            print(f"✓ {var}: {value[:10]}...{value[-5:]}")
        else:
            print(f"✓ {var}: {value}")
    else:
        print(f"✗ {var}: MISSING")
        missing.append(var)

if missing:
    print(f"\n❌ Missing variables: {', '.join(missing)}")
    print("Please add them to .env file")
else:
    print("\n✅ All configuration variables present")
EOF
```

### Step 7: Test Database Connection

```bash
# Run comprehensive database test
cd ~/visitor-counting/Visitor-Counting-System-Backend
source venv/bin/activate

python3 Test/test_setup.py
```

**Expected output:**
```
Testing Supabase connection...
✓ Supabase URL configured
✓ Service key configured
✓ Table name configured
✓ Connection successful
✓ Table 'detections' exists
✓ Table has correct schema
✓ Can insert test record
✓ Can query records

✅ All tests passed!
```

### Configuration Troubleshooting

**Problem: "ModuleNotFoundError: No module named 'dotenv'"**
```bash
pip install python-dotenv
```

**Problem: "ConnectionError: Failed to connect to Supabase"**
```bash
# Check internet connectivity
ping -c 4 rgkkadtaiivcuuvekwdo.supabase.co

# Verify SUPABASE_URL is correct
grep SUPABASE_URL .env

# Check service key is correct (should start with "eyJ")
grep SUPABASE_SERVICE_KEY .env | head -c 50
```

**Problem: "Table 'detections' does not exist"**
```bash
# Log into Supabase dashboard
# Go to Table Editor
# Verify table name is exactly "detections" (case-sensitive!)
# If different, update TABLE_NAME in .env
```

---

---

## Testing & Validation

### Pre-Flight Checklist

Before starting the server, verify everything is ready:

```bash
# ✓ Checklist
cd ~/visitor-counting/Visitor-Counting-System-Backend
source venv/bin/activate

echo "=== Pre-Flight Checklist ==="

# 1. Virtual environment active?
which python3 | grep venv && echo "✓ venv active" || echo "✗ venv NOT active"

# 2. All packages installed?
pip list | grep -E "flask|gunicorn|ultralytics|opencv|supabase" && echo "✓ Packages installed"

# 3. .env file exists?
[ -f .env ] && echo "✓ .env exists" || echo "✗ .env MISSING"

# 4. .env has correct permissions?
ls -la .env | grep "^-rw-------" && echo "✓ .env secure" || echo "⚠ .env permissions too open"

# 5. YOLO model exists?
[ -f yolov8n.pt ] && echo "✓ YOLO model present" || echo "⚠ YOLO will download on first run"

# 6. Test images exist?
[ -d testing_images ] && echo "✓ Test images available"

# 7. Can connect to Supabase?
python3 -c "from dotenv import load_dotenv; load_dotenv(); from supabase import create_client; import os; create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))" && echo "✓ Supabase connection OK"

echo "=== End Checklist ==="
```

### Test 1: Import Test

```bash
# Test all critical imports
python3 << 'EOF'
print("Testing imports...")

try:
    import cv2
    print(f"✓ OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"✗ OpenCV: {e}")

try:
    import flask
    print(f"✓ Flask: {flask.__version__}")
except ImportError as e:
    print(f"✗ Flask: {e}")

try:
    import ultralytics
    print(f"✓ Ultralytics: {ultralytics.__version__}")
except ImportError as e:
    print(f"✗ Ultralytics: {e}")

try:
    from supabase import create_client
    print(f"✓ Supabase: OK")
except ImportError as e:
    print(f"✗ Supabase: {e}")

print("\n✅ Import test complete")
EOF
```

### Test 2: Configuration Test

```bash
# Run configuration validation script
python3 Test/test_setup.py
```

**Expected output:**
```
Testing environment configuration...
✓ SUPABASE_URL: https://rgkkadtaiivcuuvekwdo.supabase.co
✓ SUPABASE_SERVICE_KEY: eyJ***
✓ TABLE_NAME: detections
✓ INGESTION_API_KEY: Z8x***

Testing Supabase connection...
✓ Connected successfully
✓ Table 'detections' accessible

✅ All configuration tests passed
```

### Test 3: Pipeline Test

```bash
# Test the full processing pipeline with a sample image
python3 Test/test_with_image.py
```

**Expected output:**
```
Loading YOLO model... (may take 10-30 seconds first time)
✓ Model loaded

Processing test image: testing_images/sevenpeople.jpg
✓ Image loaded
✓ YOLO inference complete
✓ Detected 7 people
✓ Data inserted to Supabase

Processing time: 312ms
✅ Pipeline test passed
```

### Test 4: Development Server Test

Start server in development mode:

```bash
# Make sure venv is active
source venv/bin/activate

# Start Flask development server
python3 -m server.app
```

**Expected output:**
```
INFO - Loading environment configuration...
INFO - SUPABASE_URL: https://rgkkadtaiivcuuvekwdo.supabase.co
INFO - TABLE_NAME: detections
INFO - SERVER_HOST: 0.0.0.0
INFO - SERVER_PORT: 8000

INFO - Initializing Image Processing Pipeline...
INFO - Loading YOLO model from yolov8n.pt...
Ultralytics YOLOv8.3.232 🚀 Python-3.12.1
YOLOv8n summary: 225 layers, 3,157,200 parameters

INFO - YOLO model loaded successfully
INFO - Supabase client initialized
INFO - Pipeline ready

 * Serving Flask app 'server.app'
 * Debug mode: off
INFO - WARNING: This is a development server. Do not use in production.
INFO - Use a production WSGI server like gunicorn instead.
 * Running on http://0.0.0.0:8000
 * Press CTRL+C to quit
```

**Leave server running and open NEW terminal for tests below.**

### Test 5: Health Check Test

From a **new terminal** (server still running in first terminal):

```bash
# Test from server itself
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

### Test 6: API Authentication Test

```bash
# Test with wrong API key (should fail)
curl -X POST http://localhost:8000/api/v1/process-image \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: wrong-key" \
  -d '{"image":"test","room_id":"test"}' \
  -w "\nHTTP Status: %{http_code}\n"

# Expected: HTTP Status: 401
# Response: {"error":"Invalid or missing API key"}

# Test with missing API key (should fail)
curl -X POST http://localhost:8000/api/v1/process-image \
  -H "Content-Type: application/json" \
  -d '{"image":"test","room_id":"test"}' \
  -w "\nHTTP Status: %{http_code}\n"

# Expected: HTTP Status: 401
```

### Test 7: Image Processing Test (JSON endpoint)

```bash
cd ~/visitor-counting/Visitor-Counting-System-Backend

# Test with base64-encoded image
curl -X POST http://localhost:8000/api/v1/process-image \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -d '{
    "image": "'"$(base64 -w 0 testing_images/sevenpeople.jpg)"'",
    "room_id": "test-room-001"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

# Expected: HTTP Status: 200
# Response: 
# {
#   "status": "ok",
#   "room_id": "test-room-001",
#   "people_count": 7,
#   "timestamp": "2025-11-26T...",
#   "processing_time_ms": 285
# }
```

### Test 8: Image Processing Test (Multipart endpoint)

```bash
# Test with raw JPEG file
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "file=@testing_images/sevenpeople.jpg" \
  -F "room_id=test-room-002" \
  -w "\nHTTP Status: %{http_code}\n"

# Expected: HTTP Status: 200
# Response similar to above
```

### Test 9: Validation Tests

```bash
# Test 1: Invalid room_id (special characters)
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "file=@testing_images/sevenpeople.jpg" \
  -F "room_id=room@#$%" \
  -w "\nHTTP Status: %{http_code}\n"
# Expected: 400 Bad Request

# Test 2: Missing room_id
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "file=@testing_images/sevenpeople.jpg" \
  -w "\nHTTP Status: %{http_code}\n"
# Expected: 400 Bad Request

# Test 3: Missing image file
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "room_id=test-room" \
  -w "\nHTTP Status: %{http_code}\n"
# Expected: 400 Bad Request
```

### Test 10: Network Accessibility Test

Test from another device on the same LAN:

```bash
# From your laptop/another computer on same WiFi:
# Replace <server-lan-ip> with your server's IP (e.g., 192.168.1.100)

# Test health check
curl http://<server-lan-ip>:8000/health

# Test image processing
curl -X POST http://<server-lan-ip>:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "file=@/path/to/test/image.jpg" \
  -F "room_id=laptop-test"

# If this fails:
# 1. Check firewall: sudo ufw status
# 2. Check server is listening: sudo ss -tulnp | grep :8000
# 3. Check network connectivity: ping <server-lan-ip>
```

### Test 11: Automated Test Suite

```bash
# Run comprehensive test suite
cd ~/visitor-counting/Visitor-Counting-System-Backend
source venv/bin/activate

# First, make sure development server is stopped (Ctrl+C in other terminal)

# Run all tests
python3 Test/test_server.py

# Expected output:
# Testing health endpoint...
# ✓ Health check passed
#
# Testing JSON endpoint...
# ✓ Authentication works
# ✓ Image processing works
# ✓ Person count correct (7)
# ✓ Data saved to Supabase
#
# Testing multipart endpoint...
# ✓ Multipart upload works
# ✓ Person count correct (7)
#
# ✅ All tests passed! (3/3)
```

### Test 12: Database Verification

```bash
# Verify data was inserted into Supabase
python3 << 'EOF'
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# Get last 5 records
result = client.table('detections') \
    .select('*') \
    .order('timestamp', desc=True) \
    .limit(5) \
    .execute()

print(f"Last {len(result.data)} detections:")
for record in result.data:
    print(f"  - Room: {record['room_id']}, Count: {record['people_count']}, Time: {record['timestamp']}")
EOF
```

### Test Summary Checklist

After all tests, verify:

- ✅ All Python packages import successfully
- ✅ .env configuration is correct
- ✅ Supabase connection works
- ✅ YOLO model loads and runs
- ✅ Flask server starts without errors
- ✅ Health endpoint returns 200 OK
- ✅ Authentication rejects invalid keys
- ✅ JSON endpoint processes images correctly
- ✅ Multipart endpoint processes images correctly
- ✅ Validation rejects invalid inputs
- ✅ Server accessible from other LAN devices
- ✅ Data successfully inserted to Supabase

**If ALL tests pass, you're ready for production deployment! 🚀**

---

## Production Deployment Options

### Why Not Use Flask Development Server?

❌ **Flask's built-in server is NOT production-ready:**
- Single-threaded (only one request at a time)
- No process management or auto-restart
- Poor performance under load
- No worker process management
- Not secure or optimized

✅ **Use Gunicorn (or uWSGI) for production:**
- Multi-worker support (handle concurrent requests)
- Process management and auto-reload
- Better performance and stability
- Production-tested and battle-hardened
- Integration with systemd for auto-start

### Option 1: Systemd Service (RECOMMENDED)

**Why systemd?**
- Automatic startup on boot
- Automatic restart on crash
- Log management with journald
- Resource limits and security controls
- Standard Linux service management

#### Step 1: Create Service File

```bash
# Create systemd service file
sudo nano /etc/systemd/system/visitor-counting.service
```

#### Step 2: Service Configuration

```ini
[Unit]
Description=Visitor Counting HTTP Ingestion Server
Documentation=https://github.com/wwwtriplew/Visitor-Counting-System-Backend
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=your-username
Group=your-username
WorkingDirectory=/home/your-username/visitor-counting/Visitor-Counting-System-Backend

# Environment
Environment="PATH=/home/your-username/visitor-counting/Visitor-Counting-System-Backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/home/your-username/visitor-counting/Visitor-Counting-System-Backend/.env

# Gunicorn command
ExecStart=/home/your-username/visitor-counting/Visitor-Counting-System-Backend/venv/bin/gunicorn \
    server.app:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile /home/your-username/visitor-counting/logs/access.log \
    --error-logfile /home/your-username/visitor-counting/logs/error.log \
    --capture-output

# Restart policy
Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=300

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security
PrivateTmp=yes
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/home/your-username/visitor-counting/logs

[Install]
WantedBy=multi-user.target
```

**⚠️ IMPORTANT: Replace `your-username` with your actual username!**

```bash
# Find your username
whoami

# Use sed to replace in one command:
sudo sed -i 's/your-username/'$(whoami)'/g' /etc/systemd/system/visitor-counting.service
```

#### Step 3: Create Log Directory

```bash
# Create logs directory
mkdir -p ~/visitor-counting/logs

# Set permissions
chmod 755 ~/visitor-counting/logs
```

#### Step 4: Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable visitor-counting

# Start the service
sudo systemctl start visitor-counting

# Check status
sudo systemctl status visitor-counting
```

**Expected status output:**
```
● visitor-counting.service - Visitor Counting HTTP Ingestion Server
     Loaded: loaded (/etc/systemd/system/visitor-counting.service; enabled)
     Active: active (running) since Tue 2025-11-26 10:30:15 UTC; 5s ago
   Main PID: 12345 (gunicorn)
      Tasks: 5 (limit: 4096)
     Memory: 2.1G
     CGroup: /system.slice/visitor-counting.service
             ├─12345 /home/user/visitor-counting/.../gunicorn server.app:app
             ├─12346 /home/user/visitor-counting/.../gunicorn server.app:app
             ├─12347 /home/user/visitor-counting/.../gunicorn server.app:app
             ├─12348 /home/user/visitor-counting/.../gunicorn server.app:app
             └─12349 /home/user/visitor-counting/.../gunicorn server.app:app

Nov 26 10:30:15 visitor-server gunicorn[12345]: [INFO] Starting gunicorn 21.2.0
Nov 26 10:30:15 visitor-server gunicorn[12345]: [INFO] Listening at: http://0.0.0.0:8000
Nov 26 10:30:16 visitor-server gunicorn[12345]: [INFO] Using worker: sync
Nov 26 10:30:16 visitor-server gunicorn[12346]: [INFO] Booting worker with pid: 12346
Nov 26 10:30:16 visitor-server gunicorn[12347]: [INFO] Booting worker with pid: 12347
Nov 26 10:30:16 visitor-server gunicorn[12348]: [INFO] Booting worker with pid: 12348
Nov 26 10:30:16 visitor-server gunicorn[12349]: [INFO] Booting worker with pid: 12349
```

#### Step 5: Service Management Commands

```bash
# Start service
sudo systemctl start visitor-counting

# Stop service
sudo systemctl stop visitor-counting

# Restart service (after config changes)
sudo systemctl restart visitor-counting

# Reload (graceful restart, no dropped requests)
sudo systemctl reload visitor-counting

# Check status
sudo systemctl status visitor-counting

# Enable auto-start on boot
sudo systemctl enable visitor-counting

# Disable auto-start
sudo systemctl disable visitor-counting

# View live logs
sudo journalctl -u visitor-counting -f

# View last 100 lines of logs
sudo journalctl -u visitor-counting -n 100

# View logs since yesterday
sudo journalctl -u visitor-counting --since yesterday

# View logs with timestamps
sudo journalctl -u visitor-counting -o short-precise
```

#### Step 6: Test Production Server

```bash
# Health check
curl http://localhost:8000/health

# Process test image
curl -X POST http://localhost:8000/api/v1/process-image-bytes \
  -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
  -F "file=@testing_images/sevenpeople.jpg" \
  -F "room_id=production-test"

# Check logs for request
sudo journalctl -u visitor-counting -n 20
```

### Option 2: Screen Session (For Testing)

**Use screen for:**
- Quick testing before systemd setup
- Debugging issues
- Development on remote server

**⚠️ NOT recommended for production** (no auto-restart, no monitoring)

```bash
# Install screen
sudo apt install -y screen

# Start new screen session
screen -S visitor-counting

# Activate venv
cd ~/visitor-counting/Visitor-Counting-System-Backend
source venv/bin/activate

# Start gunicorn
gunicorn server.app:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --log-level info

# Detach from screen: Press Ctrl+A, then D

# List screen sessions
screen -ls

# Reattach to session
screen -r visitor-counting

# Kill session (from inside screen)
exit
# Or kill from outside:
screen -X -S visitor-counting quit
```

### Option 3: Docker Container (Advanced)

**Create Dockerfile:**
```bash
nano ~/visitor-counting/Visitor-Counting-System-Backend/Dockerfile
```

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "server.app:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120"]
```

**Build and run:**
```bash
# Build image
docker build -t visitor-counting:latest .

# Run container
docker run -d \
    --name visitor-counting \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file .env \
    visitor-counting:latest

# Check logs
docker logs -f visitor-counting

# Stop container
docker stop visitor-counting

# Start container
docker start visitor-counting
```

### Option 4: PM2 (Alternative Process Manager)

```bash
# Install Node.js and PM2
sudo apt install -y nodejs npm
sudo npm install -g pm2

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'visitor-counting',
    cwd: '/home/user/visitor-counting/Visitor-Counting-System-Backend',
    script: 'venv/bin/gunicorn',
    args: 'server.app:app --bind 0.0.0.0:8000 --workers 4 --timeout 120',
    env: {
      PATH: '/home/user/visitor-counting/Visitor-Counting-System-Backend/venv/bin:' + process.env.PATH
    },
    autorestart: true,
    watch: false,
    max_memory_restart: '2G',
    error_file: '~/visitor-counting/logs/pm2-error.log',
    out_file: '~/visitor-counting/logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js

# Enable startup on boot
pm2 startup
pm2 save

# PM2 commands
pm2 list           # List apps
pm2 stop visitor-counting
pm2 restart visitor-counting
pm2 logs visitor-counting
pm2 monit          # Real-time monitor
```

### Comparison of Deployment Options

| Feature | Systemd | Screen | Docker | PM2 |
|---------|---------|--------|--------|-----|
| **Auto-start on boot** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Auto-restart on crash** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Log management** | ✅ Excellent | ⚠️ Basic | ✅ Good | ✅ Good |
| **Resource limits** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Setup complexity** | ⚠️ Medium | ✅ Easy | ❌ Complex | ⚠️ Medium |
| **Linux integration** | ✅ Native | ❌ No | ⚠️ Isolated | ⚠️ Node.js required |
| **Recommended for** | Production | Testing | Containers | Node.js users |

**Recommendation: Use Systemd for Ubuntu Server production deployment.**

---

## Security Hardening

### Firewall Configuration (UFW)

```bash
# Check firewall status
sudo ufw status verbose

# If inactive, enable with caution (make sure SSH is allowed first!)
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 8000/tcp comment 'HTTP Ingestion Server'
sudo ufw enable

# View rules with numbers
sudo ufw status numbered

# Delete a rule by number (if needed)
sudo ufw delete 3

# Default policies (recommended)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow from specific IP only (e.g., limit to your camera subnet)
sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp

# Block all other access to 8000
sudo ufw deny 8000/tcp

# Check final configuration
sudo ufw status verbose
```

**Expected UFW output:**
```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere          # SSH
8000/tcp                   ALLOW IN    192.168.1.0/24    # Camera subnet
8000/tcp                   DENY IN     Anywhere          # Block others
```

### File Permissions

```bash
# Secure .env file (only owner can read/write)
chmod 600 ~/visitor-counting/Visitor-Counting-System-Backend/.env

# Secure service keys and certificates
chmod 600 ~/visitor-counting/Visitor-Counting-System-Backend/yolov8n.pt

# Application code (readable by all, writable by owner)
chmod 755 ~/visitor-counting/Visitor-Counting-System-Backend/server
chmod 644 ~/visitor-counting/Visitor-Counting-System-Backend/server/*.py

# Log directory (writable by app user)
chmod 755 ~/visitor-counting/logs
```

### API Key Security

**Best practices:**
1. ✅ Use strong random keys (32+ characters)
2. ✅ Never commit keys to Git (.gitignore includes .env)
3. ✅ Rotate keys periodically (every 90 days)
4. ✅ Use different keys for dev/staging/production
5. ✅ Log failed authentication attempts

**Rotating API key:**
```bash
# Generate new key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
nano ~/visitor-counting/Visitor-Counting-System-Backend/.env
# Change INGESTION_API_KEY=new-key-here

# Restart service
sudo systemctl restart visitor-counting

# Update all cameras with new key
# (coordinate timing to minimize downtime)
```

### Fail2Ban (Intrusion Prevention)

**Install Fail2Ban to block repeated failed auth attempts:**

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Create filter for visitor-counting
sudo nano /etc/fail2ban/filter.d/visitor-counting.conf
```

```ini
[Definition]
failregex = ^.*WARNING.*Invalid API key from <HOST>.*$
ignoreregex =
```

**Create jail configuration:**
```bash
sudo nano /etc/fail2ban/jail.d/visitor-counting.conf
```

```ini
[visitor-counting]
enabled = true
port = 8000
protocol = tcp
filter = visitor-counting
logpath = /home/your-username/visitor-counting/logs/error.log
maxretry = 5
findtime = 600
bantime = 3600
action = iptables-multiport[name=visitor-counting, port="8000", protocol=tcp]
```

**Start Fail2Ban:**
```bash
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban
sudo fail2ban-client status visitor-counting
```

### SSL/TLS with Reverse Proxy (Optional)

**Why add nginx + SSL?**
- Encrypt traffic between cameras and server
- Terminate SSL at nginx (easier cert management)
- Add rate limiting and request filtering
- Better logging and monitoring

**Install nginx:**
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

**Configure nginx reverse proxy:**
```bash
sudo nano /etc/nginx/sites-available/visitor-counting
```

```nginx
server {
    listen 80;
    server_name visitor-server.local;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name visitor-server.local;

    # SSL configuration (self-signed for LAN)
    ssl_certificate /etc/nginx/ssl/visitor-counting.crt;
    ssl_certificate_key /etc/nginx/ssl/visitor-counting.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logging
    access_log /var/log/nginx/visitor-counting-access.log;
    error_log /var/log/nginx/visitor-counting-error.log;

    # Rate limiting (10 requests per second per IP)
    limit_req_zone $binary_remote_addr zone=visitor_limit:10m rate=10r/s;
    limit_req zone=visitor_limit burst=20 nodelay;

    # Max upload size
    client_max_body_size 15M;

    # Proxy to gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

**Generate self-signed certificate (for LAN):**
```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/visitor-counting.key \
    -out /etc/nginx/ssl/visitor-counting.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=visitor-server.local"

# Enable site
sudo ln -s /etc/nginx/sites-available/visitor-counting /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Update firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### SSH Security

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no (after setting up SSH keys)
# Set: Port 2222 (optional: change from default port 22)

# Restart SSH
sudo systemctl restart sshd

# Setup SSH keys (from your laptop)
ssh-keygen -t ed25519
ssh-copy-id user@192.168.1.100
```

### System Updates

```bash
# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure update behavior
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
```

### Monitoring Security Events

```bash
# Monitor failed login attempts
sudo journalctl -u ssh | grep "Failed password"

# Monitor API auth failures
sudo journalctl -u visitor-counting | grep "Invalid API key"

# Check fail2ban status
sudo fail2ban-client status

# View banned IPs
sudo fail2ban-client status visitor-counting
```

---

## Camera Integration

### Supported Camera Types

1. **IP Cameras with HTTP POST** (Best compatibility)
   - Axis, Hikvision, Dahua, Reolink, etc.
   - Configure in camera web interface

2. **RTSP Cameras with Script**
   - Any RTSP camera
   - Use script to capture frames and POST

3. **USB/Local Cameras**
   - Webcams, USB cameras
   - Capture with ffmpeg/v4l2

4. **Mobile Phones as Cameras**
   - IP Webcam app (Android)
   - iVCam (iOS)

### Server Endpoints

**Base URL:**
```
http://<server-lan-ip>:8000
```

**Endpoints:**
1. `GET /health` - Health check (no auth)
2. `POST /api/v1/process-image` - JSON with base64 image
3. `POST /api/v1/process-image-bytes` - Multipart with raw JPEG

### Camera Configuration Requirements

**Required Headers:**
```
X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI
```

**Required Fields:**
- `file` or `image`: JPEG image data
- `room_id`: Alphanumeric identifier (e.g., "lobby", "room-101")
- `timestamp`: (Optional) ISO 8601 UTC timestamp

**Image Specifications:**
- Format: JPEG
- Max size: 10 MB
- Recommended resolution: 640x480 to 1920x1080
- Recommended quality: 80-90%
- Frame rate: 1 image per 60 seconds (or as needed)

### Method 1: IP Camera Built-in HTTP POST

**Example: Hikvision Camera**

1. Login to camera web interface
2. Go to: Configuration → Event → Basic Event → HTTP Listening
3. Enable: HTTP Listening
4. Set URL: `http://192.168.1.100:8000/api/v1/process-image-bytes`
5. Set Method: POST
6. Set Headers: `X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`
7. Set Interval: 60 seconds

**Example: Axis Camera**

1. Login to camera
2. Go to: System → Events → Recipients
3. Add HTTP Recipient:
   - URL: `http://192.168.1.100:8000/api/v1/process-image-bytes`
   - Method: POST
   - Authentication: Custom header
   - Header: `X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI`

### Method 2: RTSP Camera with Python Script

```python
#!/usr/bin/env python3
"""Camera capture script for RTSP cameras"""
import cv2
import requests
import time
from datetime import datetime
import sys

# Configuration
RTSP_URL = "rtsp://admin:password@192.168.1.201:554/stream1"
SERVER_URL = "http://192.168.1.100:8000/api/v1/process-image-bytes"
API_KEY = "Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI"
ROOM_ID = "camera-01"
CAPTURE_INTERVAL = 60  # seconds

def capture_and_send():
    """Capture frame from RTSP and send to server"""
    # Open RTSP stream
    cap = cv2.VideoCapture(RTSP_URL)
    
    if not cap.isOpened():
        print(f"[{datetime.now()}] ERROR: Cannot open RTSP stream")
        return False
    
    # Read frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print(f"[{datetime.now()}] ERROR: Failed to read frame")
        return False
    
    # Encode as JPEG
    _, img_encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    
    # Send to server
    try:
        response = requests.post(
            SERVER_URL,
            headers={'X-API-KEY': API_KEY},
            files={'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')},
            data={'room_id': ROOM_ID},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[{datetime.now()}] SUCCESS: {result['people_count']} people detected")
            return True
        else:
            print(f"[{datetime.now()}] ERROR: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
        return False

if __name__ == "__main__":
    print(f"Starting camera capture for {ROOM_ID}")
    print(f"Server: {SERVER_URL}")
    print(f"Interval: {CAPTURE_INTERVAL}s")
    
    while True:
        capture_and_send()
        time.sleep(CAPTURE_INTERVAL)
```

**Deploy script:**
```bash
# Save script
nano ~/visitor-counting/scripts/camera_capture.py
chmod +x ~/visitor-counting/scripts/camera_capture.py

# Install opencv if needed
pip install opencv-python requests

# Test manually
python3 ~/visitor-counting/scripts/camera_capture.py

# Run with systemd (create separate service)
sudo nano /etc/systemd/system/camera-capture.service
```

### Method 3: Bash Script for USB/Local Cameras

```bash
#!/bin/bash
# Camera capture script for local USB camera

API_KEY="Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI"
SERVER="http://192.168.1.100:8000"
ROOM_ID="office-entrance"
DEVICE="/dev/video0"  # Adjust for your camera
INTERVAL=60

while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Capture image with ffmpeg
    ffmpeg -y -f v4l2 -i "$DEVICE" -frames 1 -q:v 3 /tmp/snapshot.jpg 2>/dev/null
    
    if [ -f /tmp/snapshot.jpg ]; then
        # Send to server
        response=$(curl -s -w "\n%{http_code}" -X POST "$SERVER/api/v1/process-image-bytes" \
            -H "X-API-KEY: $API_KEY" \
            -F "file=@/tmp/snapshot.jpg" \
            -F "room_id=$ROOM_ID")
        
        http_code=$(echo "$response" | tail -n 1)
        body=$(echo "$response" | head -n -1)
        
        if [ "$http_code" = "200" ]; then
            count=$(echo "$body" | jq -r '.people_count' 2>/dev/null || echo "?")
            echo "[$TIMESTAMP] ✓ Sent image, detected $count people"
        else
            echo "[$TIMESTAMP] ✗ Error: HTTP $http_code - $body"
        fi
        
        rm /tmp/snapshot.jpg
    else
        echo "[$TIMESTAMP] ✗ Failed to capture image"
    fi
    
    sleep $INTERVAL
done
```

**Deploy bash script:**
```bash
# Save script
nano ~/visitor-counting/scripts/usb_camera.sh
chmod +x ~/visitor-counting/scripts/usb_camera.sh

# Install dependencies
sudo apt install -y ffmpeg jq

# Test
~/visitor-counting/scripts/usb_camera.sh
```

### Method 4: Mobile Phone as Camera

**Android - IP Webcam App:**
1. Install "IP Webcam" from Play Store
2. Configure:
   - Resolution: 1280x720
   - Quality: 85%
   - FPS Limit: 1
3. Start server (note IP address)
4. Create capture script:

```bash
#!/bin/bash
PHONE_IP="192.168.1.150"
PHONE_PORT="8080"
SERVER="http://192.168.1.100:8000"
API_KEY="Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI"
ROOM_ID="mobile-camera"

while true; do
    # Download snapshot from phone
    curl -s "http://$PHONE_IP:$PHONE_PORT/shot.jpg" -o /tmp/phone_snapshot.jpg
    
    if [ -s /tmp/phone_snapshot.jpg ]; then
        # Send to server
        curl -X POST "$SERVER/api/v1/process-image-bytes" \
            -H "X-API-KEY: $API_KEY" \
            -F "file=@/tmp/phone_snapshot.jpg" \
            -F "room_id=$ROOM_ID"
        
        echo "[$(date)] Sent frame from phone"
    fi
    
    sleep 60
done
```

### Testing Camera Integration

```bash
# Test 1: Manual image send
curl -X POST http://192.168.1.100:8000/api/v1/process-image-bytes \
    -H "X-API-KEY: Z8xN7vK2pQ9wL5mR3jT6hF4nY1cX8gS0uE7bV9dA2oI" \
    -F "file=@test_image.jpg" \
    -F "room_id=test-camera" \
    -v

# Test 2: Check server logs for camera requests
sudo journalctl -u visitor-counting -f | grep "process-image"

# Test 3: Verify data in Supabase
python3 << 'EOF'
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
result = client.table('detections').select('*').order('timestamp', desc=True).limit(10).execute()

for r in result.data:
    print(f"{r['timestamp']} | {r['room_id']} | {r['people_count']} people")
EOF
```

### Camera Troubleshooting

**Problem: Camera can't reach server**
```bash
# From camera network, test connectivity:
ping 192.168.1.100
curl http://192.168.1.100:8000/health

# Check firewall on server:
sudo ufw status | grep 8000
```

**Problem: Authentication fails**
```bash
# Verify API key matches:
grep INGESTION_API_KEY ~/visitor-counting/Visitor-Counting-System-Backend/.env

# Check server logs for auth errors:
sudo journalctl -u visitor-counting | grep "Invalid API key"
```

**Problem: Images rejected (413 error)**
```bash
# Check image size:
ls -lh /tmp/snapshot.jpg

# Reduce image quality in capture script:
ffmpeg ... -q:v 5 ...  # Higher number = lower quality = smaller file
```

## Monitoring & Logging

### System Monitoring

**Check service health:**
```bash
# Service status
sudo systemctl status visitor-counting

# Is service running?
systemctl is-active visitor-counting  # Output: active or inactive

# Is service enabled for boot?
systemctl is-enabled visitor-counting  # Output: enabled or disabled

# Restart count (how many times has it crashed?)
systemctl show visitor-counting -p NRestarts

# Memory usage
systemctl show visitor-counting -p MemoryCurrent
```

**Check network connectivity:**
```bash
# Is server listening on port 8000?
sudo ss -tulnp | grep :8000
# Expected: tcp LISTEN 0 4096 0.0.0.0:8000 0.0.0.0:* users:(("gunicorn",...))

# Active connections to server
sudo ss -tn | grep :8000

# Connection statistics
sudo netstat -s | grep -E "(connections|requests)"
```

**Resource monitoring:**
```bash
# CPU and memory (interactive)
htop
# Look for gunicorn processes (should see 4-5 workers)

# CPU usage by service
systemctl status visitor-counting | grep "CPU:"

# Memory usage by service
systemctl status visitor-counting | grep "Memory:"

# Disk space
df -h
# Ensure / has >10% free space

# Disk I/O
sudo iotop -o
# Look for high write activity (could indicate logging issues)

# Network bandwidth
iftop -i wlan0
# Shows real-time network traffic
```

### Log Management

**Viewing logs:**
```bash
# Real-time logs (follow)
sudo journalctl -u visitor-counting -f

# Last 100 lines
sudo journalctl -u visitor-counting -n 100

# Logs from last hour
sudo journalctl -u visitor-counting --since "1 hour ago"

# Logs from today
sudo journalctl -u visitor-counting --since today

# Logs between time range
sudo journalctl -u visitor-counting --since "2025-11-26 10:00" --until "2025-11-26 11:00"

# Show only errors
sudo journalctl -u visitor-counting -p err

# Show with full output (no truncation)
sudo journalctl -u visitor-counting --no-pager

# Export logs to file
sudo journalctl -u visitor-counting --since today > ~/visitor-counting-logs-$(date +%Y%m%d).txt
```

**Application logs:**
```bash
# Access log (successful requests)
tail -f ~/visitor-counting/logs/access.log

# Error log (errors and warnings)
tail -f ~/visitor-counting/logs/error.log

# Both logs simultaneously
tail -f ~/visitor-counting/logs/*.log

# Count requests per minute
grep "$(date +"%d/%b/%Y:%H:%M")" ~/visitor-counting/logs/access.log | wc -l

# Count errors in last hour
find ~/visitor-counting/logs -name "*.log" -mmin -60 -exec grep -i "error" {} + | wc -l
```

**Log rotation (prevent disk fill-up):**
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/visitor-counting
```

```
/home/username/visitor-counting/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 username username
    postrotate
        systemctl reload visitor-counting >/dev/null 2>&1 || true
    endscript
}
```

**Test logrotate:**
```bash
sudo logrotate -d /etc/logrotate.d/visitor-counting  # Dry run
sudo logrotate -f /etc/logrotate.d/visitor-counting  # Force rotation
```

### Performance Metrics

**Request statistics:**
```bash
# Count total requests today
grep "$(date +%Y-%m-%d)" ~/visitor-counting/logs/access.log | wc -l

# Requests per hour (last 24 hours)
for hour in {0..23}; do
    h=$(printf "%02d" $hour)
    count=$(grep "$(date +%Y-%m-%d):$h:" ~/visitor-counting/logs/access.log | wc -l)
    echo "Hour $h: $count requests"
done

# Average response time (if logged)
grep "processing_time" ~/visitor-counting/logs/access.log | awk '{sum+=$NF; count++} END {print "Avg:", sum/count, "ms"}'

# Failed requests (4xx, 5xx)
grep -E "HTTP/[0-9.]+ [45][0-9]{2}" ~/visitor-counting/logs/access.log | wc -l
```

**System resources:**
```bash
# Create monitoring script
cat > ~/visitor-counting/scripts/monitor.sh << 'EOF'
#!/bin/bash
echo "=== Visitor Counting Server Monitor ==="
echo "Time: $(date)"
echo ""

# Service status
echo "Service Status:"
systemctl is-active visitor-counting && echo "  ✓ Running" || echo "  ✗ Stopped"
echo ""

# Resource usage
echo "Resource Usage:"
pid=$(systemctl show visitor-counting -p MainPID | cut -d= -f2)
if [ "$pid" != "0" ]; then
    ps -p $pid -o %cpu,%mem,rss,etime,comm --no-headers |
    awk '{printf "  CPU: %.1f%%  Memory: %.1f%% (%.0f MB)  Uptime: %s\n", $1, $2, $3/1024, $4}'
fi
echo ""

# Disk space
echo "Disk Space:"
df -h / | tail -1 | awk '{printf "  Used: %s / %s (%s)\n", $3, $2, $5}'
echo ""

# Active connections
echo "Active Connections:"
count=$(sudo ss -tn | grep :8000 | wc -l)
echo "  $count active connections"
echo ""

# Recent errors
echo "Recent Errors (last hour):"
errors=$(sudo journalctl -u visitor-counting --since "1 hour ago" -p err --no-pager | wc -l)
echo "  $errors errors logged"

EOF
chmod +x ~/visitor-counting/scripts/monitor.sh

# Run monitor
~/visitor-counting/scripts/monitor.sh
```

### Advanced Monitoring with Prometheus (Optional)

**Install Prometheus node exporter:**
```bash
# Download node exporter
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/

# Create systemd service
sudo nano /etc/systemd/system/node_exporter.service
```

```ini
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=nobody
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start node exporter
sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter

# Verify (metrics available at http://localhost:9100/metrics)
curl http://localhost:9100/metrics | head -20
```

### Alerting Script

**Create alert script for critical issues:**
```bash
cat > ~/visitor-counting/scripts/alert.sh << 'EOF'
#!/bin/bash
# Alert if service is down or resource usage is high

SERVICE="visitor-counting"
EMAIL="admin@example.com"  # Configure email
LOG_FILE="$HOME/visitor-counting/logs/alerts.log"

# Check if service is running
if ! systemctl is-active $SERVICE >/dev/null; then
    echo "[$(date)] ALERT: $SERVICE is DOWN!" | tee -a "$LOG_FILE"
    # Send email (requires mailutils)
    # echo "Service $SERVICE is down" | mail -s "ALERT: $SERVICE Down" "$EMAIL"
fi

# Check CPU usage (alert if >80%)
cpu=$(systemctl show $SERVICE -p CPUUsageNSec --value)
if [ $cpu -gt 80 ]; then
    echo "[$(date)] WARNING: High CPU usage: $cpu%" | tee -a "$LOG_FILE"
fi

# Check disk space (alert if <10%)
usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $usage -gt 90 ]; then
    echo "[$(date)] WARNING: Low disk space: $usage% used" | tee -a "$LOG_FILE"
fi

EOF
chmod +x ~/visitor-counting/scripts/alert.sh

# Add to crontab (run every 5 minutes)
crontab -e
# Add: */5 * * * * /home/username/visitor-counting/scripts/alert.sh
```

### Dashboard (Simple HTML)

**Create basic status dashboard:**
```bash
cat > ~/visitor-counting/scripts/generate_dashboard.sh << 'EOF'
#!/bin/bash
# Generate HTML dashboard with server status

OUTPUT="/tmp/visitor-dashboard.html"

cat > "$OUTPUT" << 'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>Visitor Counting Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial; margin: 20px; background: #f0f0f0; }
        .metric { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .ok { color: green; }
        .warn { color: orange; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Visitor Counting Server Status</h1>
    <p>Last updated: $(date)</p>
HTML

# Service status
if systemctl is-active visitor-counting >/dev/null; then
    echo '<div class="metric ok">✓ Service Running</div>' >> "$OUTPUT"
else
    echo '<div class="metric error">✗ Service Down</div>' >> "$OUTPUT"
fi

# Recent requests
requests=$(grep "$(date +%Y-%m-%d)" ~/visitor-counting/logs/access.log 2>/dev/null | wc -l)
echo "<div class='metric'>Requests today: $requests</div>" >> "$OUTPUT"

# System resources
echo "<div class='metric'>$(free -h | grep Mem | awk '{print "Memory: " $3 " / " $2}')</div>" >> "$OUTPUT"
echo "<div class='metric'>$(df -h / | tail -1 | awk '{print "Disk: " $3 " / " $2 " (" $5 " used)"}')</div>" >> "$OUTPUT"

echo "</body></html>" >> "$OUTPUT"

echo "Dashboard generated: $OUTPUT"
EOF
chmod +x ~/visitor-counting/scripts/generate_dashboard.sh

# Run and view
~/visitor-counting/scripts/generate_dashboard.sh
firefox /tmp/visitor-dashboard.html  # Or copy to web server
```

## Troubleshooting

### Server won't start

```bash
# Check logs
sudo journalctl -u visitor-counting -n 100

# Test manually
cd ~/visitor-counting/Visitor-Counting-System-Backend
source venv/bin/activate
python3 -m server.app
```

### OpenCV errors

```bash
# Verify headless version
pip list | grep opencv

# Should show opencv-python-headless, NOT opencv-python
# If opencv-python is installed, remove it:
pip uninstall opencv-python -y
pip install opencv-python-headless
```

### Camera can't connect

```bash
# Check firewall
sudo ufw status

# Check server is listening
sudo ss -tulnp | grep :8000

# Test from server itself
curl http://localhost:8000/health
```

### High CPU usage

```bash
# Reduce gunicorn workers
# Edit /etc/systemd/system/visitor-counting.service
# Change --workers 4 to --workers 2

sudo systemctl daemon-reload
sudo systemctl restart visitor-counting
```

## Maintenance

### Update Code

```bash
cd ~/visitor-counting/Visitor-Counting-System-Backend
git pull origin main

# Restart service
sudo systemctl restart visitor-counting
```

### Update Dependencies

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart visitor-counting
```

### Rotate Logs

Add to crontab:
```bash
crontab -e
```

Add:
```
0 0 * * 0 sudo journalctl --vacuum-time=7d
```

## Security Notes

1. **Keep API key secret** - Only share with authorized cameras
2. **LAN only** - Server should NOT be exposed to internet
3. **Regular updates** - Keep Ubuntu and packages updated
4. **Monitor logs** - Check for unauthorized access attempts

---

**Next Steps:**
1. Fill in the actual LAN IP, WiFi SSID, and password at the top
2. SSH into the server and follow this guide
3. Configure cameras to POST to the server
4. Monitor logs to verify everything works

**Server will be accessible at:** `http://<lan-ip>:8000`
