# TorShift

Advanced Tor-Based Dynamic IP Rotation Framework for authorized security research and penetration testing.

```
████████╗ ██████╗ ██████╗ ███████╗██╗  ██╗██╗███████╗████████╗
╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝██║  ██║██║██╔════╝╚══██╔══╝
   ██║   ██║   ██║██████╔╝███████╗███████║██║█████╗     ██║   
   ██║   ██║   ██║██╔══██╗╚════██║██╔══██║██║██╔══╝     ██║   
   ██║   ╚██████╔╝██║  ██║███████║██║  ██║██║██║        ██║   
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   v2.1.0
```

## Overview

TorShift is a Python-based framework designed for security professionals to perform authorized penetration testing with enhanced anonymity through dynamic IP rotation via the Tor network. The tool provides **automatic IP rotation every 5 minutes**, comprehensive logging, and OPSEC-focused features for legitimate security research.

[![asciicast](https://asciinema.org/a/UrIh7dD9zoVGGfkE5qdeGir2P.svg)](https://asciinema.org/a/UrIh7dD9zoVGGfkE5qdeGir2P)


## Key Features

- **Automatic IP Rotation**: Built-in 5-minute interval rotation with background monitoring
- **Real-time IP Changes**: Seamlessly switches between Tor exit nodes for maximum anonymity  
- **Multi-Service IP Verification**: Uses multiple services to verify current external IP
- **Comprehensive Logging**: Detailed operational logs with timestamps and rotation metrics
- **Interactive Interface**: Command-line interface for real-time operations
- **Proxy Integration**: ProxyChains4 configuration for external tool integration
- **Security Compliance**: Follows security standards (CWE-200, CWE-319, OWASP ASVS)
- **DNS Leak Protection**: Built-in DNS leak detection and prevention
- **Circuit Analysis**: Detailed Tor circuit path information
- **Automated Operations**: Background rotation with configurable intervals (default 5 minutes)

## Quick Start

### Automatic Setup
```bash
# Clone and setup TorShift
git clone https://github.com/0nsec/TorShift.git
cd TorShift
chmod +x setup.sh
./setup.sh
```

### Start Automatic IP Rotation (5 minutes)
```bash
# Start auto-rotation with 5-minute intervals
python3 torshift.py --auto-rotate 300

# Or use interactive mode with all features
python3 torshift.py --interactive
```

### Execute Commands Through Rotating Proxy
```bash
# Execute nmap through Tor with automatic IP rotation
python3 torshift.py --execute "nmap -sS target.example.com"

# Execute curl to check current IP
python3 torshift.py --execute "curl -s https://httpbin.org/ip"
```
### System Requirements
- Linux operating system (Ubuntu/Debian recommended)
- Python 3.7+
- Tor service
- ProxyChains4

## Installation

### 1. Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Tor and ProxyChains4
sudo apt install tor proxychains4 python3-pip

# Start and enable Tor service
sudo systemctl start tor
sudo systemctl enable tor
```

### 2. Configure Tor

Edit Tor configuration file:
```bash
sudo nano /etc/tor/torrc
```

Add the following configuration:
```
# Control port configuration
ControlPort 9051
HashedControlPassword 16:AEBC98175E7F4A913FD516F2CCAC1B6382F0BB8C44DACFB7BB5AE31F4B
CookieAuthentication 1

# SOCKS proxy
SOCKSPort 9050

# Circuit configuration
NewCircuitPeriod 120
MaxCircuitDirtiness 300
CircuitBuildTimeout 60

# Exit node preferences
ExitNodes {us},{gb},{de},{ca},{au},{se},{nl},{ch}
StrictNodes 0

# Exclude problematic countries
ExcludeExitNodes {cn},{ru},{kp},{ir},{sy},{by}
ExcludeNodes {cn},{ru},{kp},{ir},{sy},{by}
```

Restart Tor service:
```bash
sudo systemctl restart tor
```

### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Verify Installation and Test Auto-Rotation

```bash
# Verify all components and see the ASCII banner
python3 torshift.py --verify-install

# 🔥 Start automatic IP rotation (5-minute intervals)
python3 torshift.py --auto-rotate 300

# Interactive mode with full control
python3 torshift.py --interactive
```

### Interactive Mode

Launch the interactive interface:
```bash
python3 torshift.py --interactive
```

### Command Line Options

```bash
# 🔄 Auto-rotation every 5 minutes (recommended)
python3 torshift.py --auto-rotate 300

# 🎯 Single IP rotation
python3 torshift.py --rotate-once

# 🖥️ Interactive mode with all features
python3 torshift.py --interactive

# ⚡ Execute command through rotating proxy
python3 torshift.py --execute "curl -s https://httpbin.org/ip"

# 🔍 Test connectivity through Tor
python3 torshift.py --test-connectivity

# 🛡️ DNS leak test
python3 torshift.py --dns-test

# 📊 Generate operational report
python3 torshift.py --generate-report

# 🌍 Exclude specific countries
python3 torshift.py --exclude-countries CN,RU,KP,IR --auto-rotate 300
```

### Integration with Security Tools

TorShift automatically configures ProxyChains for seamless integration:

```bash
# Use with nmap (automatic IP rotation in background)
proxychains4 -f /tmp/torshift_proxychains.conf nmap -sS target.example.com

# Use with curl
proxychains4 -f /tmp/torshift_proxychains.conf curl -s https://httpbin.org/ip

# Use with any security tool while IP rotates every 5 minutes
proxychains4 -f /tmp/torshift_proxychains.conf your-security-tool

# Or execute directly through TorShift for automatic proxy configuration
python3 torshift.py --execute "your-security-tool"
```
### OPSEC Guidelines
- Verify IP rotation between operations
- Monitor for DNS leaks regularly
- Use appropriate rotation intervals for your use case
- Avoid predictable patterns in testing activities
- Keep detailed logs for compliance purposes

### Country Exclusions
The tool automatically excludes exit nodes from high-risk countries by default:
- China (CN)
- Russia (RU)
- North Korea (KP)
- Iran (IR)
- Syria (SY)
- Belarus (BY)

## Advanced Configuration

### Auto-Rotation Settings
```bash
# Configuration via environment variables
export TORSHIFT_ROTATION_INTERVAL=300  # 5 minutes
export TORSHIFT_MAX_ATTEMPTS=3
export TORSHIFT_BLOCKED_COUNTRIES="CN,RU,KP,IR,SY,BY"

# Or use command line options
python3 torshift.py --auto-rotate 300 --exclude-countries CN,RU,KP,IR
```

### Monitoring Rotation Status
```bash
# Generate detailed operational report
python3 torshift.py --generate-report

# Expected output includes:
# - Current IP and rotation count
# - Uptime and rotation metrics  
# - Previous IPs used
# - Blocked countries list
# - Auto-rotation status
```

### Environment Variables
- `TOR_CONTROL_PORT`: Tor control port (default: 9051)
- `TOR_PROXY_PORT`: Tor SOCKS port (default: 9050)
- `TOR_PASSWORD`: Tor control password

### Log Files
Logs are stored in `~/.torshift/logs/` with timestamps for audit purposes.

## Troubleshooting

### Common Issues

1. **Tor service not running**:
   ```bash
   sudo systemctl status tor
   sudo systemctl start tor
   ```

2. **Control port authentication failed**:
   - Verify Tor configuration in `/etc/tor/torrc`
   - Check control port password setup

3. **IP rotation not working**:
   - Verify Tor circuits are building properly
   - Check network connectivity
   - Ensure sufficient exit nodes available

4. **DNS leaks detected**:
   - Verify DNS configuration
   - Check ProxyChains configuration
   - Ensure system DNS is not bypassing proxy

### Standards Compliance
- **CWE-200**: Information Exposure Prevention
- **CWE-319**: Cleartext Transmission Mitigation  
- **OWASP ASVS V9.2.1**: Network Communications Security
- **NIST SP 800-115**: Information Security Testing Compliance

## Author

Developed by 0nsec Security Research Team for the security community.
Remember: This tool is for authorized security professionals only. Use responsibly.

```
██████╗ ███╗   ██╗███████╗███████╗ ██████╗
██╔═████╗████╗  ██║██╔════╝██╔════╝██╔════╝
██║██╔██║██╔██╗ ██║███████╗█████╗  ██║     
████╔╝██║██║╚██╗██║╚════██║██╔══╝  ██║     
╚██████╔╝██║ ╚████║███████║███████╗╚██████╗
 ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚══════╝ ╚═════╝
```
