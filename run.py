
#%%
import json 
import argparse
import subprocess
import os

mullvad_rules_template = """
define RESOLVER_ADDRS = {
  100.100.100.100
}

define EXCLUDED_IPS = {
    <EXCLUDED_IPS>
}

define EXCLUDED_IPV6 = {
    <EXCLUDED_IPV6>
}

table inet mullvad-ts {
  chain excludeOutgoing {
    type route hook output priority 0; policy accept;
    ip daddr $EXCLUDED_IPS ct mark set 0x00000f41 meta mark set 0x6d6f6c65;
    ip6 daddr $EXCLUDED_IPV6 ct mark set 0x00000f41 meta mark set 0x6d6f6c65;
  }

  chain allow-incoming {
    type filter hook input priority -100; policy accept;
    iifname "tailscale0" ct mark set 0x00000f41 meta mark set 0x6d6f6c65;
  }

  chain excludeDns {
    type filter hook output priority -10; policy accept;
    ip daddr $RESOLVER_ADDRS udp dport 53 ct mark set 0x00000f41 meta mark set 0x6d6f6c65;
    ip daddr $RESOLVER_ADDRS tcp dport 53 ct mark set 0x00000f41 meta mark set 0x6d6f6c65;
  }
}

"""




def execute_cmd(cmd, parse_json=False):
    print(cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    errors = p.stderr.readlines()

    result = [line.decode().replace('\n','') for line in p.stdout.readlines()]

    if parse_json:
        result = json.loads(''.join(result))
        
    if errors:
        print(errors)
    return result




def collect_tailscale_ips():
    tailscale_json = execute_cmd("tailscale status --json", parse_json=True)
    
    ipv4 = []
    ipv6 = []
    
    def append_ip(ip):
        if ':' in ip:
            ipv6.append(ip)
        else:
            ipv4.append(ip)

    for ip in tailscale_json["Self"]["TailscaleIPs"]:
        append_ip(ip)

    
    for d in tailscale_json["Peer"].values():
        for ip in d["TailscaleIPs"]:
            append_ip(ip)
    
    return {'ipv4':ipv4, 'ipv6':ipv6}


# %%


def write_mullvad_file(tailscale_ips):
    mullvad_rules = mullvad_rules_template.replace("<EXCLUDED_IPS>", ', '.join(tailscale_ips['ipv4'])).replace("<EXCLUDED_IPV6>", ', '.join(tailscale_ips['ipv6'])) 

    filename = os.path.join(os.path.dirname(__file__), 'mullvad.rules')
    with open(filename, 'w') as file:
        file.write(mullvad_rules)
        print(f'Saved {filename}')
    return filename
        
# %%

def find_running_processes(process_names):
    # import here, such that only users who exclude some processes need this import
    import psutil
    matches = []
    for process in psutil.process_iter ():
        for process_name in process_names:
            if process_name in process.name():
                matches.append({'name':process.name (), 'pid':process.pid})
                
    return matches

def split_tunnel(process_names):      
    matches = find_running_processes(process_names)  
    for match in matches:
        execute_cmd(f"mullvad split-tunnel pid add  {match['pid']}")   
        print(f"-> Excluded '{match['name']}' from mullvad")


# %%
def add(exclude=None):       
    if exclude:
        split_tunnel(exclude)
    tailscale_ips = collect_tailscale_ips()        
    mullvad_rules_filename = write_mullvad_file(tailscale_ips)
    execute_cmd(f"sudo nft -f '{mullvad_rules_filename}'")               
    print('Applied rules')
    
                
def remove():
    execute_cmd("sudo nft delete table inet mullvad-ts")
    print('Removed rules')

# %%


parser = argparse.ArgumentParser(description='Sets nft rules such mullvad is compatible with tailscale')
parser.add_argument('--remove',  action='store_true',
                    help='Remove the nft rules (default: Add the nft rules)')
parser.add_argument('--exclude',  nargs='*' , help='Names of the processes that should circumvent the VPN')

args = parser.parse_args()
if args.remove:
    remove()
else:
    add(exclude=args.exclude)
    
# %%
