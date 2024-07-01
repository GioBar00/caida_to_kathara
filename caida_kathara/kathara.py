# Stdlib
import os
from typing import Mapping
import string
# External packages
import ast

from caida_kathara.defines import GEN_PATH
from caida_kathara.util import write_file, calculate_great_circle_latency
from caida_kathara.common import (
    ArgsCaidaDicts,
    docker_image,
)
from caida_kathara.net import NetworkDescription, IPNetwork

KATHARA_LAB_CONF = 'lab.conf'


class KatharaLabGenArgs(ArgsCaidaDicts):
    def __init__(self, args, caida_dicts,
                 networks: Mapping[IPNetwork, NetworkDescription]):
        """
        :param object args: Contains the passed command line arguments as named attributes.
        :param dict caida_dicts: The generated topo dicts from TopoGenerator.
        :param dict networks: The generated networks from SubnetGenerator.
        """
        super().__init__(args, caida_dicts)
        self.networks = networks


class KatharaLabGenerator(object):

    def __init__(self, args):
        """
        :param KatharaLabGenArgs args: Contains the passed command line arguments and topo dicts.
        """
        self.args = args
        self.lab_conf = ""
        self.devices_ifids = {}
        self.device_info = {}
        self.net_ids = {}
        self.next_net_id = "0"
        self.alphabet = string.digits + string.ascii_lowercase
        self.link_br_ifids = {}

        self.if_name = "net" if self.args.megalos else "eth"
    
    def _increment_net_id(self, idx):
        if idx < 0:
            self.next_net_id = self.alphabet[0] + self.next_net_id
        elif self.next_net_id[idx] == self.alphabet[-1]:
            self.next_net_id = self.next_net_id[:idx] + self.alphabet[0] + self.next_net_id[idx + 1:]
            self._increment_net_id(idx - 1)
        else:
            self.next_net_id = self.next_net_id[:idx] + self.alphabet[self.alphabet.index(self.next_net_id[idx]) + 1] + self.next_net_id[idx + 1:]

    def generate_lab(self):
        self._initiate_lab()
        self._assign_networks()
        self._add_container_images()
        self._add_commands()
        self._write_lab()

    def _initiate_lab(self):
        self.lab_conf += f'LAB_DESCRIPTION="Caida to Kathará: {str(self.args.caida_config).split("/")[-1]}"\n'
        self.lab_conf += f'LAB_AUTHOR="ETH Zurich"\n'
        self.lab_conf += f'LAB_VERSION=1.0\n'
        self.lab_conf += f'LAB_WEB="http://example.com"\n'
        self.lab_conf += '\n'

    def _assign_networks(self):
        self.lab_conf += '# Collision domains\n'
        gen_lines = []
        for net, desc in self.args.networks.items():
            if net not in self.net_ids:
                self.net_ids[net] = self.next_net_id
                self._increment_net_id(len(self.next_net_id) - 1)   
            coll_domain = f"{self.net_ids[net]}"
            self.link_br_ifids[desc.name] = {}
            for br_name, ip in desc.ip_net.items():
                if br_name not in self.devices_ifids:
                    self.devices_ifids[br_name] = 0
                # Add collision domain to lab.conf
                gen_lines.append(f'{br_name}[{self.devices_ifids[br_name]}]="{coll_domain}"\n')
                if br_name not in self.device_info:
                    self.device_info[br_name] = {
                        "startup": "",
                        "shutdown": "",
                    }
                # Add IP addresses to startup script
                if ip.version == 4:
                    self.device_info[br_name][
                        "startup"] += f'ip addr add {ip} dev {self.if_name}{self.devices_ifids[br_name]}\n'
                else:
                    self.device_info[br_name][
                        "startup"] += f'ip -6 addr add {ip} dev {self.if_name}{self.devices_ifids[br_name]}\n'
                    
                self.link_br_ifids[desc.name][br_name] = self.devices_ifids[br_name]

                self.devices_ifids[br_name] += 1

        gen_lines.sort()
        for line in gen_lines:
            self.lab_conf += line
        self.lab_conf += '\n'

    def _add_container_images(self):
        self.lab_conf += '# Container images\n'
        gen_lines = []
        for _, as_conf in self.args.caida_dicts.items():
            for br_name in as_conf["routers"].keys():
                image = docker_image(self.args, 'base')
                gen_lines.append(f'{br_name}[image]="{image}"\n')

        gen_lines.sort()
        for line in gen_lines:
            self.lab_conf += line
        self.lab_conf += '\n'

    def _add_commands(self):
        for _, as_conf in self.args.caida_dicts.items():
            for local_br, desc in as_conf["routers"].items():
                # Add startup commands
                #self.device_info[br_name]["local_br"] += "sleep 2s\n"
                
                # Add shutdown commands
                #self.device_info[br_name]["local_br"] += f'sleep 1s\n'
                pass

        for _, desc in self.args.networks.items():
            local_br, remote_br = ast.literal_eval(desc.name)
            assert local_br != remote_br
            if not are_same_as(local_br, remote_br):
                continue
            as_id = int(local_br.split("_")[0][2:])
            lat1 = self.args.caida_dicts[as_id]["routers"][local_br]["latitude"]
            lon1 = self.args.caida_dicts[as_id]["routers"][local_br]["longitude"]
            lat2 = self.args.caida_dicts[as_id]["routers"][remote_br]["latitude"]
            lon2 = self.args.caida_dicts[as_id]["routers"][remote_br]["longitude"]
            delay = calculate_great_circle_latency(lat1, lon1, lat2, lon2)
            self._add_delay_to_interface(local_br, self.link_br_ifids[desc.name][local_br], delay)
            self._add_delay_to_interface(remote_br, self.link_br_ifids[desc.name][remote_br], delay)
          
    def _add_delay_to_interface(self, br_name, if_id, delay):
        self.device_info[br_name]["startup"] += f'tc qdisc add dev {self.if_name}{if_id} root netem delay {delay}ms\n'
        #self.device_info[br_name]["shutdown"] += f'tc qdisc del dev {self.if_name}{if_id} root\n'
        pass 

    def _write_lab(self):
        write_file(os.path.join(self.args.output_dir, KATHARA_LAB_CONF), self.lab_conf)
        for dev_id, info in self.device_info.items():
            write_file(os.path.join(self.args.output_dir, f"{dev_id}.startup"), info["startup"])
            if info["shutdown"]:
                write_file(os.path.join(self.args.output_dir, f"{dev_id}.shutdown"), info["shutdown"])

def are_same_as(br1, br2):
    return br1.split("_")[0] == br2.split("_")[0]