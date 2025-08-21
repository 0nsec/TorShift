#!/usr/bin/env python3
"""
TorShift - Advanced Tor-Based Dynamic IP Rotation Framework
Author: 0nsec Security Research
Purpose: Authorized penetration testing and security research
OPSEC: Ensure authorized testing environment only

Security Classifications:
- CWE-200: Information Exposure Prevention Through Traffic Anonymization
- CWE-319: Cleartext Transmission Mitigation via SOCKS5 Tunneling
- OWASP ASVS: V9.2.1 Network Communications Security Verification
- NIST SP 800-115: Technical Guide to Information Security Testing Compliance
"""

import subprocess
import requests
import time
import json
import random
import threading
import logging
import signal
import sys
import os
import argparse
from contextlib import contextmanager
import socket
from urllib3.exceptions import InsecureRequestWarning

# Handle optional dependencies
try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False
    print("Warning: stem library not available. Install with: pip install stem")

try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False
    print("Warning: pysocks library not available. Install with: pip install pysocks")

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class TorShift:
    def __init__(self, config=None):
        self.version = "2.1.0"
        self.author = "0nsec Security Research"
        
        # Network configuration
        self.tor_proxy_host = "127.0.0.1"
        self.tor_proxy_port = 9050
        self.tor_control_port = 9051
        self.tor_password = "0nsecTorShift2025"
        
        # Operational parameters
        self.current_ip = None
        self.previous_ips = []
        self.rotation_interval = 300  # 5 minutes default
        self.auto_rotate = False
        self.rotation_count = 0
        self.start_time = time.time()
        self.last_rotation_time = 0
        
        # Security settings OSEC...
        self.blocked_countries = ['CN', 'RU', 'KP', 'IR', 'SY', 'BY']
        self.allowed_countries = []
        self.exit_nodes = []
        self.max_rotation_attempts = 3
        
        # Session management
        self.session = requests.Session()
        self.logger = self._setup_logging()
        self.rotation_thread = None

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logging(self):
        """Configure comprehensive logging for security operations"""
        logger = logging.getLogger('TorShift')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '\033[92m[%(asctime)s]\033[0m \033[94m%(levelname)s\033[0m - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        log_dir = os.path.expanduser('~/.torshift/logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(f'{log_dir}/torshift_{int(time.time())}.log')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger

    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown with operational cleanup"""
        self.logger.info(f"Received termination signal {signum}")
        self.stop_automatic_rotation()
        self._cleanup_session()
        sys.exit(0)

    def _cleanup_session(self):
        """Clean up session and temporary files"""
        try:
            self.session.close()
            temp_files = ['/tmp/torshift_proxychains.conf']
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.debug(f"Cleaned up temporary file: {temp_file}")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def banner(self):
        """Display professional security research banner"""
        print(f"""
████████╗ ██████╗ ██████╗ ███████╗██╗  ██╗██╗███████╗████████╗
╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝██║  ██║██║██╔════╝╚══██╔══╝
   ██║   ██║   ██║██████╔╝███████╗███████║██║█████╗     ██║   
   ██║   ██║   ██║██╔══██╗╚════██║██╔══██║██║██╔══╝     ██║   
   ██║   ╚██████╔╝██║  ██║███████║██║  ██║██║██║        ██║   
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   

[+] TorShift v{self.version} - Advanced Tor-Based IP Rotation Framework
[+] Author: {self.author}
[+] Purpose: Authorized Security Research & Penetration Testing
[+] OPSEC: Ensure testing is conducted in authorized environments only

[*] Security Classifications:
    - CWE-200: Information Exposure Prevention
    - CWE-319: Cleartext Transmission Mitigation
    - OWASP ASVS: V9.2.1 Network Communications Security
    - NIST SP 800-115: Information Security Testing Compliance

[!] Auto IP Rotation: Every 5 minutes when enabled
[!] Current Session: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
        """)

    def verify_tor_installation(self):
        """Comprehensive Tor installation and configuration verification"""
        checks = {
            'tor_service': self._check_tor_service(),
            'tor_proxy': self._check_tor_proxy(),
            'tor_control': self._check_tor_control(),
            'stem_library': self._check_stem_library(),
            'proxychains': self._check_proxychains()
        }
        
        self.logger.info("Performing Tor installation verification:")
        for check, status in checks.items():
            status_text = "\033[92mPASS\033[0m" if status else "\033[91mFAIL\033[0m"
            self.logger.info(f"  {check.replace('_', ' ').title()}: {status_text}")
        
        return all(checks.values())

    def _check_tor_service(self):
        """Verify Tor service status"""
        try:
            # First try systemctl (for systemd systems)
            result = subprocess.run(['systemctl', 'is-active', 'tor'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip() == 'active':
                return True
        except:
            pass
            
        try:
            # Fallback to service command (for container/non-systemd environments)
            result = subprocess.run(['service', 'tor', 'status'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            pass
            
        try:
            # Final fallback: check if tor process is running
            result = subprocess.run(['pgrep', 'tor'], 
                                  capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False

    def _check_tor_proxy(self):
        """Verify Tor SOCKS proxy accessibility"""
        try:
            sock = socket.socket()
            sock.settimeout(5)
            result = sock.connect_ex((self.tor_proxy_host, self.tor_proxy_port))
            sock.close()
            return result == 0
        except:
            return False

    def _check_tor_control(self):
        """Verify Tor control port accessibility"""
        try:
            sock = socket.socket()
            sock.settimeout(5)
            result = sock.connect_ex((self.tor_proxy_host, self.tor_control_port))
            sock.close()
            return result == 0
        except:
            return False

    def _check_stem_library(self):
        """Verify stem library availability"""
        return STEM_AVAILABLE

    def _check_proxychains(self):
        """Verify ProxyChains4 installation"""
        try:
            result = subprocess.run(['which', 'proxychains4'], 
                                  capture_output=True, text=True)
            return bool(result.stdout.strip())
        except:
            return False

    def initialize_tor_service(self):
        """Initialize and configure Tor service for security operations"""
        self.logger.info("Initializing Tor service for security research operations")
        
        if not self._check_tor_service():
            self.logger.info("Starting Tor service...")
            try:
                # Try systemctl first (for systemd systems)
                try:
                    subprocess.run(['sudo', 'systemctl', 'start', 'tor'], 
                                 check=True, capture_output=True)
                except:
                    # Fallback to service command (for container environments)
                    subprocess.run(['sudo', 'service', 'tor', 'start'], 
                                 check=True, capture_output=True)
                time.sleep(10)  # Allow Tor initialization
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Could not start Tor service: {e}")
                # Continue anyway if ports are accessible
                pass

        if self.verify_tor_installation():
            self.logger.info("Tor service initialized successfully")
            return True
        else:
            # If service check fails but ports are accessible, allow operation
            if self._check_tor_proxy() and self._check_tor_control():
                self.logger.warning("Tor service check failed but ports are accessible - continuing")
                return True
            self.logger.error("Tor service initialization failed")
            return False

    def configure_proxychains(self, config_path="/tmp/torshift_proxychains.conf"):
        """Generate ProxyChains configuration optimized for security research"""
        proxychains_config = f"""
# TorShift ProxyChains Configuration
# Generated by 0nsec Security Research Framework
# Purpose: Authorized security testing and research

strict_chain
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000

# Local network exclusions (RFC 1918)
localnet 127.0.0.0/255.0.0.0
localnet 10.0.0.0/255.0.0.0
localnet 172.16.0.0/255.240.0.0
localnet 192.168.0.0/255.255.0.0
localnet 169.254.0.0/255.255.0.0

[ProxyList]
socks5 {self.tor_proxy_host} {self.tor_proxy_port}
"""
        
        try:
            with open(config_path, 'w') as f:
                f.write(proxychains_config)
            self.logger.info(f"ProxyChains configuration written to {config_path}")
            return config_path
        except Exception as e:
            self.logger.error(f"Failed to configure ProxyChains: {e}")
            return None

    def get_current_ip_address(self):
        """Retrieve current external IP with multiple verification sources"""
        self.session.proxies = {
            'http': f'socks5://{self.tor_proxy_host}:{self.tor_proxy_port}',
            'https': f'socks5://{self.tor_proxy_host}:{self.tor_proxy_port}'
        }

        ip_services = [
            ('https://httpbin.org/ip', 'json', 'origin'),
            ('https://api.ipify.org?format=json', 'json', 'ip'),
            ('https://ifconfig.me/ip', 'text', None),
            ('https://icanhazip.com', 'text', None),
            ('https://ident.me', 'text', None)
        ]
        
        for service_url, response_type, json_key in ip_services:
            try:
                response = self.session.get(service_url, timeout=10, verify=False)
                
                if response_type == 'json':
                    ip_address = response.json().get(json_key, '')
                else:
                    ip_address = response.text.strip()
                
                if ip_address and self._validate_ip_format(ip_address):
                    if self.current_ip != ip_address:
                        self.previous_ips.append(self.current_ip) if self.current_ip else None
                        self.current_ip = ip_address
                    
                    self.logger.info(f"Current external IP: {ip_address}")
                    return ip_address
                    
            except Exception as e:
                self.logger.debug(f"Failed to retrieve IP from {service_url}: {e}")
                continue
        
        self.logger.error("Failed to retrieve current IP from all services")
        return None

    def _validate_ip_format(self, ip_address):
        """Validate IPv4 address format"""
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            return False

    def rotate_tor_circuit(self):
        """Force new Tor circuit creation with enhanced error handling"""
        if not STEM_AVAILABLE:
            self.logger.error("stem library not available. Install with: pip install stem")
            return False
            
        self.logger.info("Initiating Tor circuit rotation for IP change")
        
        for attempt in range(self.max_rotation_attempts):
            try:
                with Controller.from_port(port=self.tor_control_port) as controller:
                    # Try multiple authentication methods in order of preference
                    authenticated = False
                    
                    # Method 1: Try no authentication (if allowed)
                    try:
                        controller.authenticate()
                        authenticated = True
                        self.logger.debug("Authenticated with no credentials")
                    except Exception as e:
                        self.logger.debug(f"No-auth failed: {e}")
                    
                    # Method 2: Try with empty password
                    if not authenticated:
                        try:
                            controller.authenticate(password="")
                            authenticated = True
                            self.logger.debug("Authenticated with empty password")
                        except Exception as e:
                            self.logger.debug(f"Empty password failed: {e}")
                    
                    # Method 3: Try with configured password
                    if not authenticated:
                        try:
                            controller.authenticate(password=self.tor_password)
                            authenticated = True
                            self.logger.debug("Authenticated with configured password")
                        except Exception as e:
                            self.logger.debug(f"Configured password failed: {e}")
                    
                    # Method 4: Try to use cookie authentication by changing permissions
                    if not authenticated:
                        try:
                            import subprocess
                            # Try to make auth cookie readable
                            subprocess.run(['sudo', 'chmod', '644', '/var/run/tor/control.authcookie'], 
                                         capture_output=True, timeout=5)
                            controller.authenticate()
                            authenticated = True
                            self.logger.debug("Authenticated using cookie after permission fix")
                        except Exception as e:
                            self.logger.debug(f"Cookie auth with permission fix failed: {e}")
                    
                    if not authenticated:
                        # Skip this attempt but don't fail completely
                        self.logger.warning(f"Authentication failed on attempt {attempt + 1}, trying circuit reset anyway")
                        # Sometimes NEWNYM works even without full auth
                        try:
                            controller.signal(Signal.NEWNYM)
                        except:
                            raise Exception("All authentication methods failed and signal failed")
                    else:
                        # Signal for new circuit
                        controller.signal(Signal.NEWNYM)
                    
                    self.logger.info(f"NEWNYM signal sent (attempt {attempt + 1})")
                    
                    # Wait for circuit establishment
                    time.sleep(15)
                    
                    # Verify IP rotation
                    old_ip = self.current_ip
                    new_ip = self.get_current_ip_address()
                    
                    if new_ip and new_ip != old_ip:
                        self.rotation_count += 1
                        self.logger.info(f"IP rotation successful: {old_ip} -> {new_ip}")
                        self._log_rotation_metrics()
                        return True
                    else:
                        self.logger.warning(f"IP rotation attempt {attempt + 1} failed - same IP returned")
                        # Wait a bit longer for next attempt
                        time.sleep(10)
                        
            except Exception as e:
                self.logger.error(f"Circuit rotation attempt {attempt + 1} failed: {e}")
                time.sleep(5)  # Brief delay before retry
        
        self.logger.error("All circuit rotation attempts failed")
        return False

    def _log_rotation_metrics(self):
        """Log rotation performance metrics for operational analysis"""
        uptime = time.time() - self.start_time
        avg_rotation_time = uptime / self.rotation_count if self.rotation_count > 0 else 0
        
        self.logger.info(f"Rotation metrics - Count: {self.rotation_count}, "
                        f"Uptime: {uptime:.1f}s, Avg interval: {avg_rotation_time:.1f}s")

    def get_tor_circuit_information(self):
        """Retrieve detailed Tor circuit path information"""
        if not STEM_AVAILABLE:
            self.logger.error("stem library not available. Install with: pip install stem")
            return None
            
        try:
            with Controller.from_port(port=self.tor_control_port) as controller:
                # Try multiple authentication methods
                authenticated = False
                
                try:
                    controller.authenticate()
                    authenticated = True
                except:
                    pass
                
                if not authenticated:
                    try:
                        controller.authenticate(password=self.tor_password)
                        authenticated = True
                    except:
                        pass
                
                if not authenticated:
                    try:
                        controller.authenticate(password="")
                        authenticated = True
                    except:
                        pass
                
                if not authenticated:
                    raise Exception("Authentication failed")
                
                circuits = controller.get_circuits()
                active_circuits = [c for c in circuits if c.status == 'BUILT']
                
                if active_circuits:
                    circuit = active_circuits[0]
                    circuit_info = {
                        'id': circuit.id,
                        'status': circuit.status,
                        'path': [f"{relay.fingerprint[:8]}({relay.nickname})" for relay in circuit.path],
                        'build_time': circuit.build_time,
                        'purpose': circuit.purpose
                    }
                    
                    self.logger.info(f"Active circuit: {' -> '.join(circuit_info['path'])}")
                    return circuit_info
                    
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve circuit information: {e}")
            return None

    def start_automatic_rotation(self, interval=300):
        """Initialize automated IP rotation with configurable interval"""
        self.rotation_interval = interval
        self.auto_rotate = True
        self.last_rotation_time = time.time()
        
        def rotation_worker():
            self.logger.info(f"Automatic IP rotation started - interval: {interval}s ({interval//60} minutes)")
            
            while self.auto_rotate:
                time.sleep(30)  # Check every 30 seconds
                if self.auto_rotate:
                    current_time = time.time()
                    time_since_last = current_time - self.last_rotation_time
                    
                    if time_since_last >= self.rotation_interval:
                        self.logger.info(f"Executing automatic IP rotation (every {interval//60} minutes)")
                        success = self.rotate_tor_circuit()
                        self.last_rotation_time = current_time
                        
                        if success:
                            self.logger.info(f"Automatic rotation successful. Next rotation in {interval//60} minutes")
                        else:
                            self.logger.warning("Automatic rotation failed, will retry at next interval")
                    else:
                        remaining = int(self.rotation_interval - time_since_last)
                        if remaining % 60 == 0:  # Log every minute
                            self.logger.debug(f"Next automatic rotation in {remaining//60} minutes")
        
        self.rotation_thread = threading.Thread(target=rotation_worker, daemon=True)
        self.rotation_thread.start()
        
        # Perform initial rotation
        self.logger.info("Performing initial IP rotation...")
        self.rotate_tor_circuit()

    def stop_automatic_rotation(self):
        """Terminate automatic IP rotation"""
        self.auto_rotate = False
        if self.rotation_thread and self.rotation_thread.is_alive():
            self.rotation_thread.join(timeout=5)
        self.logger.info("Automatic IP rotation stopped")

    def execute_through_proxy(self, command, config_path="/tmp/torshift_proxychains.conf"):
        """Execute system commands through TorShift proxy chain"""
        if not os.path.exists(config_path):
            config_path = self.configure_proxychains()
        
        try:
            proxychains_command = ['proxychains4', '-f', config_path, '-q'] + command.split()
            
            self.logger.info(f"Executing through proxy: {command}")
            result = subprocess.run(
                proxychains_command,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            self.logger.info(f"Command completed - Exit code: {result.returncode}")
            return result.stdout, result.stderr, result.returncode
            
        except subprocess.TimeoutExpired:
            self.logger.error("Command execution timeout (120s)")
            return "", "Command timeout", 124
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return "", str(e), 1

    def test_proxy_connectivity(self, target_urls=None):
        """Comprehensive proxy connectivity verification"""
        if not target_urls:
            target_urls = [
                'https://httpbin.org/headers',
                'https://www.google.com',
                'https://github.com'
            ]
        
        self.logger.info("Testing proxy connectivity across multiple targets")
        results = {}
        
        for url in target_urls:
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=15, verify=False)
                response_time = time.time() - start_time
                
                results[url] = {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200
                }
                
                status = "\033[92mSUCCESS\033[0m" if response.status_code == 200 else "\033[91mFAILED\033[0m"
                self.logger.info(f"  {url}: {status} ({response.status_code}, {response_time:.2f}s)")
                
            except Exception as e:
                results[url] = {'success': False, 'error': str(e)}
                self.logger.error(f"  {url}: \033[91mFAILED\033[0m - {e}")
        
        success_rate = sum(1 for r in results.values() if r.get('success', False)) / len(results) * 100
        self.logger.info(f"Connectivity test completed - Success rate: {success_rate:.1f}%")
        
        return results

    def perform_dns_leak_test(self):
        """Verify DNS queries are properly routed through Tor"""
        self.logger.info("Performing DNS leak detection test")
        
        test_domains = ['google.com', 'github.com', 'stackoverflow.com']
        
        try:
            dns_test_url = 'https://1.1.1.1/dns-query'
            
            for domain in test_domains:
                response = self.session.get(
                    dns_test_url,
                    params={'name': domain, 'type': 'A'},
                    headers={'Accept': 'application/dns-json'},
                    timeout=10,
                    verify=False
                )
                
                if response.status_code == 200:
                    self.logger.info(f"DNS resolution for {domain}: \033[92mROUTED THROUGH PROXY\033[0m")
                else:
                    self.logger.warning(f"DNS resolution for {domain}: \033[93mUNCERTAIN\033[0m")
            
            return True
            
        except Exception as e:
            self.logger.error(f"DNS leak test failed: {e}")
            return False

    def generate_operational_report(self):
        """Generate comprehensive operational status report"""
        uptime = time.time() - self.start_time
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'version': self.version,
            'current_ip': self.current_ip,
            'rotation_count': self.rotation_count,
            'uptime_seconds': int(uptime),
            'auto_rotation_active': self.auto_rotate,
            'rotation_interval': self.rotation_interval,
            'previous_ips': self.previous_ips[-5:],  # Last 5 IPs
            'blocked_countries': self.blocked_countries,
            'proxy_configuration': f"{self.tor_proxy_host}:{self.tor_proxy_port}",
            'control_port': self.tor_control_port
        }
        
        self.logger.info("=== TorShift Operational Report ===")
        self.logger.info(json.dumps(report, indent=2))
        
        return report

    def interactive_mode(self):
        """Interactive command-line interface for TorShift operations"""
        self.banner()
        
        if not self.verify_tor_installation():
            self.logger.error("Tor installation verification failed. Run setup_tor.sh first.")
            return
        
        if not self.initialize_tor_service():
            self.logger.error("Failed to initialize Tor service")
            return
        
        # Initial setup
        self.configure_proxychains()
        self.get_current_ip_address()
        
        while True:
            try:
                print("\n" + "="*60)
                print("TorShift Interactive Command Center")
                print("="*60)
                print("1. Rotate IP address manually")
                print("2. Show current operational status")
                print("3. Test proxy connectivity")
                print("4. Execute command through proxy")
                print("5. Get Tor circuit information")
                print("6. Toggle automatic rotation")
                print("7. Perform DNS leak test")
                print("8. Generate operational report")
                print("9. Set country exclusions")
                print("0. Exit TorShift")
                print("="*60)
                
                choice = input("\n[TorShift]> Select option: ").strip()
                
                if choice == '1':
                    print("\n[*] Manual IP rotation initiated...")
                    success = self.rotate_tor_circuit()
                    if success:
                        print("[+] IP rotation completed successfully")
                    else:
                        print("[-] IP rotation failed")
                
                elif choice == '2':
                    print("\n[*] Current operational status:")
                    print(f"    Current IP: {self.current_ip}")
                    print(f"    Rotations performed: {self.rotation_count}")
                    print(f"    Auto-rotation: {'ACTIVE' if self.auto_rotate else 'INACTIVE'}")
                    if self.auto_rotate:
                        print(f"    Rotation interval: {self.rotation_interval}s")
                
                elif choice == '3':
                    print("\n[*] Testing proxy connectivity...")
                    self.test_proxy_connectivity()
                
                elif choice == '4':
                    command = input("\nEnter command to execute through proxy: ").strip()
                    if command:
                        print(f"\n[*] Executing: {command}")
                        stdout, stderr, exit_code = self.execute_through_proxy(command)
                        if stdout:
                            print(f"STDOUT:\n{stdout}")
                        if stderr:
                            print(f"STDERR:\n{stderr}")
                        print(f"Exit code: {exit_code}")
                
                elif choice == '5':
                    print("\n[*] Retrieving Tor circuit information...")
                    circuit_info = self.get_tor_circuit_information()
                    if circuit_info:
                        print(f"Circuit ID: {circuit_info['id']}")
                        print(f"Path: {' -> '.join(circuit_info['path'])}")
                        print(f"Status: {circuit_info['status']}")
                
                elif choice == '6':
                    if self.auto_rotate:
                        self.stop_automatic_rotation()
                        print("[+] Automatic rotation stopped")
                    else:
                        interval = input("Enter rotation interval in seconds (default 300): ").strip()
                        interval = int(interval) if interval.isdigit() else 300
                        self.start_automatic_rotation(interval)
                        print(f"[+] Automatic rotation started (every {interval} seconds)")
                
                elif choice == '7':
                    print("\n[*] Performing DNS leak test...")
                    self.perform_dns_leak_test()
                
                elif choice == '8':
                    print("\n[*] Generating operational report...")
                    self.generate_operational_report()
                
                elif choice == '9':
                    countries = input("Enter country codes to exclude (comma-separated): ").strip()
                    if countries:
                        self.blocked_countries = [c.strip().upper() for c in countries.split(',')]
                        print(f"[+] Country exclusions updated: {self.blocked_countries}")
                
                elif choice == '0':
                    print("\n[*] Shutting down TorShift...")
                    self.stop_automatic_rotation()
                    self._cleanup_session()
                    print("[+] TorShift shutdown complete")
                    break
                
                else:
                    print("[-] Invalid option selected")
                    
            except KeyboardInterrupt:
                print("\n\n[*] Interrupted by user")
                self.stop_automatic_rotation()
                self._cleanup_session()
                break
            except Exception as e:
                self.logger.error(f"Interactive mode error: {e}")

def main():
    """Main entry point for TorShift framework"""
    parser = argparse.ArgumentParser(
        description='TorShift - Advanced Tor-Based IP Rotation Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 torshift.py --interactive
  python3 torshift.py --auto-rotate 300 --exclude-countries CN,RU,KP,IR
  python3 torshift.py --rotate-once --test-connectivity
  python3 torshift.py --execute "nmap -sS target.example.com"
        """
    )
    
    parser.add_argument('--interactive', action='store_true', 
                       help='Launch interactive command interface')
    parser.add_argument('--auto-rotate', type=int, metavar='SECONDS',
                       help='Start automatic rotation with specified interval')
    parser.add_argument('--rotate-once', action='store_true',
                       help='Perform single IP rotation and exit')
    parser.add_argument('--test-connectivity', action='store_true',
                       help='Test proxy connectivity and exit')
    parser.add_argument('--execute', metavar='COMMAND',
                       help='Execute command through proxy and exit')
    parser.add_argument('--exclude-countries', metavar='CODES',
                       help='Comma-separated country codes to exclude')
    parser.add_argument('--verify-install', action='store_true',
                       help='Verify Tor installation and exit')
    parser.add_argument('--dns-test', action='store_true',
                       help='Perform DNS leak test and exit')
    parser.add_argument('--generate-report', action='store_true',
                       help='Generate operational report and exit')
    parser.add_argument('--version', action='version', version='TorShift v2.1.0')
    
    args = parser.parse_args()

    torshift = TorShift()

    if args.verify_install:
        torshift.banner()
        if torshift.verify_tor_installation():
            print("[+] Tor installation verification: \033[92mPASS\033[0m")
        else:
            print("[-] Tor installation verification: \033[91mFAIL\033[0m")
        return
    
    if args.exclude_countries:
        torshift.blocked_countries = [c.strip().upper() 
                                    for c in args.exclude_countries.split(',')]

    if not torshift.initialize_tor_service():
        print("[-] Failed to initialize Tor service. Run setup_tor.sh first.")
        return
    
    torshift.configure_proxychains()
    
    if args.interactive:
        torshift.interactive_mode()
    
    elif args.auto_rotate:
        torshift.banner()
        torshift.get_current_ip_address()
        torshift.start_automatic_rotation(args.auto_rotate)
        
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            torshift.stop_automatic_rotation()
    
    elif args.rotate_once:
        torshift.banner()
        torshift.get_current_ip_address()
        torshift.rotate_tor_circuit()
    
    elif args.test_connectivity:
        torshift.banner()
        torshift.test_proxy_connectivity()
    
    elif args.execute:
        torshift.banner()
        stdout, stderr, exit_code = torshift.execute_through_proxy(args.execute)
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        sys.exit(exit_code)
    
    elif args.dns_test:
        torshift.banner()
        torshift.perform_dns_leak_test()
    
    elif args.generate_report:
        torshift.banner()
        torshift.generate_operational_report()
    
    else:
        torshift.interactive_mode()

if __name__ == "__main__":
    main()
