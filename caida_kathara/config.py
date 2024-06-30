# Copyright 2014 ETH Zurich
# Copyright 2018 ETH Zurich, Anapaya Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
:mod:`config` --- SCION topology config generator
=============================================
"""
# Stdlib
import configparser
import json
import logging
import os
import sys
from io import StringIO
from typing import Mapping
import xml.etree.ElementTree as et

from caida_kathara.defines import (
    NETWORKS_FILE,
)
from caida_kathara.util import write_file
from caida_kathara.common import ArgsBase
from caida_kathara.kathara import KatharaLabGenerator, KatharaLabGenArgs
from caida_kathara.net import (
    NetworkDescription,
    IPNetwork,
    SubnetGenerator,
)
from caida_kathara.topo import TopoGenArgs, TopoGenerator


class ConfigGenArgs(ArgsBase):
    pass


class ConfigGenerator(object):
    """
    Configuration and/or topology generator.
    """

    def __init__(self, args):
        """
        Initialize an instance of the class ConfigGenerator.

        :param ConfigGenArgs args: Contains the passed command line arguments.
        """
        self.args = args
        with open(self.args.caida_config) as f:
            self.caida_config = et.parse(f)
        
        self.subnet_gen4 = SubnetGenerator(self.args.network)
        self.subnet_gen6 = SubnetGenerator(self.args.network_v6)


    def generate_all(self):
        """
        Generate all needed files.
        """
        caida_dicts, self.all_networks = self._generate_topology()
        self.networks = remove_v4_nets(self.all_networks)
        self._generate_kathara(caida_dicts)
        self._write_networks_conf(self.networks, NETWORKS_FILE)      

    def _generate_topology(self):
        topo_gen = TopoGenerator(self._topo_args())
        return topo_gen.generate()

    def _topo_args(self):
        return TopoGenArgs(self.args, self.caida_config, self.subnet_gen4,
                           self.subnet_gen6)
    
    def _generate_kathara(self, caida_dicts):
        args = self._kathara_args(caida_dicts)
        kathara_gen = KatharaLabGenerator(args)
        kathara_gen.generate_lab()

    def _kathara_args(self, caida_dicts):
        return KatharaLabGenArgs(self.args, caida_dicts, self.networks)

    def _write_networks_conf(self,
                             networks: Mapping[IPNetwork, NetworkDescription],
                             out_file: str):
        config = configparser.ConfigParser(interpolation=None)
        for net, net_desc in networks.items():
            sub_conf = {}
            for prog, ip_net in net_desc.ip_net.items():
                sub_conf[prog] = str(ip_net.ip)
            config[str(net)] = sub_conf
        text = StringIO()
        config.write(text)
        write_file(os.path.join(self.args.output_dir, out_file), text.getvalue())


def remove_v4_nets(nets: Mapping[IPNetwork, NetworkDescription]
                   ) -> Mapping[IPNetwork, NetworkDescription]:
    res = {}
    for net, net_desc in nets.items():
        if net_desc.name.endswith('_v4'):
            continue
        res[net] = net_desc
    return res
