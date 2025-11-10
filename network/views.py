from django.shortcuts import render
from .models import NumberSet
from django.http import HttpResponse
from .models import NumberSet
import re
import random
import time
from datetime import datetime
from .forms import DHCPForm

LEASE_TIME = 3600
LEASES = {}

def dhcp_view(request):
    assigned_ip = None
    lease_info = None
    if request.method == 'POST':
        form = DHCPForm(request.POST)
        if form.is_valid():
            mac = form.cleaned_data['mac_address']
            version = form.cleaned_data['dhcp_version']
            if validate_mac(mac) and validate_dhcp_version(version):
                ip = assign_ipv4(mac) if version == 'DHCPv4' else assign_ipv6(mac)
                lease_info = {
                    "mac_address": mac,
                    "assigned_ip": ip,
                    "dhcp_version": version,
                    "bitwise": mac_sum_even_or_odd(mac),
                    "lease_time": "3600 seconds",
                    "lease_start": datetime.utcnow().isoformat(),
                }

                NumberSet.objects.create(
                            mac_address=mac,
                            assigned_ip=ip,
                            dhcp_version=version,
                            bitwise=mac_sum_even_or_odd(mac),
                            lease_time="3600 seconds",
                            lease_start=datetime.utcnow().isoformat()
                        )   
            else:
                form.add_error(None, "Invalid MAC or DHCP version.")
    else:
        form = DHCPForm()
    return render(request, 'dhcp_result.html', {'form': form, 'lease_info': lease_info})

def validate_mac(mac):
    return re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac)

def validate_dhcp_version(version):
    return version in ['DHCPv4', 'DHCPv6']

def assign_ipv4(mac):
    entry = LEASES.get(mac)
    # Reuse existing lease only if it's still valid and was issued for DHCPv4
    if entry and time.time() - entry['timestamp'] < LEASE_TIME and entry.get('version') == 'DHCPv4':
        return entry['ip']
    ip = f"192.168.1.{random.randint(2, 254)}"
    LEASES[mac] = {'ip': ip, 'timestamp': time.time(), 'version': 'DHCPv4'}
    return ip

def assign_ipv6(mac):
    entry = LEASES.get(mac)
    # Reuse existing lease only if it's still valid and was issued for DHCPv6
    if entry and time.time() - entry['timestamp'] < LEASE_TIME and entry.get('version') == 'DHCPv6':
        return entry['ip']
    mac_bytes = [int(b, 16) for b in mac.split(":")]
    mac_bytes[0] ^= 0b00000010 
    eui64 = mac_bytes[:3] + [0xFF, 0xFE] + mac_bytes[3:]
    ipv6 = "2001:db8::" + ''.join(f"{b:02x}" for b in eui64[:2]) + ":" + ''.join(f"{b:02x}" for b in eui64[2:4]) + ":" + ''.join(f"{b:02x}" for b in eui64[4:6]) + ":" + ''.join(f"{b:02x}" for b in eui64[6:])
    LEASES[mac] = {'ip': ipv6, 'timestamp': time.time(), 'version': 'DHCPv6'}
    return ipv6

def mac_sum_even_or_odd(mac):
    total = sum(int(b, 16) for b in mac.split(":"))
    return "even" if total & 1 == 0 else "odd"

def list_leases(request):
    sets = NumberSet.objects.all().order_by('-created_at')

    output = "<h2>Row:</h2><br>"
    for s in sets:
        output += f"""
        mac_address: {s.mac_address}
        <br>
        assigned_ipv6: {s.assigned_ip}
        <br>
        dhcp_version: {s.dhcp_version}
        <br>
        bitwise: {s.bitwise}
        <br>
        lease_time: {s.lease_time}
        <br>
        lease_start: {s.lease_start}
        <br>
        <br>
        """
    return HttpResponse(output)

