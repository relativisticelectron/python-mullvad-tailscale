# python-mullvad-tailscale

This is a simple script that allows you to run MullvadVPN along with Tailscale. 

The script will not start tailscale or mullvad, but simply configure the nftables to allow both to work


## Requirements


- [install mullvad](https://mullvad.net/download/) in your system so you have the [mullvad cli](https://mullvad.net/en/help/how-use-mullvad-cli/) command available.
- You will also neeed `nftables` package installed.
- `tailscale` with its proper setup.


## Setup

1. Clone this repo:

```bash
git clone https://github.com/relativisticelectron/python-mullvad-tailscale.git
```

2. `pip install psutil`

## Usage


1. Run `python run.py` . If you want that some (running) applications bypass mullvad run `python run.py --exclude program_name1 program_name2` 


2. To remove the nftables run `python run.py --remove` 
