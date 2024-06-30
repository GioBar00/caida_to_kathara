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
:mod:`topo` --- SCION topology topo generator
=============================================
"""
# Stdlib
import json
import logging
import os
import random
import sys
from collections import defaultdict
from itertools import combinations

# External packages
import xml.etree.ElementTree as et

from caida_kathara.util import write_file
from caida_kathara.common import (
    ArgsBase,
    join_host_port,
    LinkRel,
)
from caida_kathara.net import (
    SubnetGenerator
)

ADDR_TYPE_4 = 'IPv4'
ADDR_TYPE_6 = 'IPv6'


class TopoGenArgs(ArgsBase):
    def __init__(self,
                 args: ArgsBase,
                 caida_config,
                 subnet_gen4: SubnetGenerator,
                 subnet_gen6: SubnetGenerator,):
        """
        :param ArgsBase args: Contains the passed command line arguments.
        :param dict caida_config: The parsed caida config.
        :param SubnetGenerator subnet_gen4: The default network generator for IPv4.
        :param SubnetGenerator subnet_gen6: The default network generator for IPv6.
        """
        super().__init__(args)
        
        self.caida_config_root = caida_config.getroot()
        self.subnet_gen = {
            ADDR_TYPE_4: subnet_gen4,
            ADDR_TYPE_6: subnet_gen6,
        }


class TopoGenerator(object):
    def __init__(self, args):
        """
        :param TopoGenArgs args: Contains the passed command line arguments.
        """
        self.args = args
        self.caida_dicts = {}
        self.hosts = []
        self.virt_addrs = set()
        self.as_list = defaultdict(list)
        self.links = defaultdict(list)
        self.assigned_br_per_as = defaultdict(dict)

        self._caiada_config_dict()

    def _caiada_config_dict(self):
        self.args.caida_config_dict = {
            "ASes": {},
            "links": []
        }
        for elem in self.args.caida_config_root:
            if elem.tag == 'property':
                self.args.caida_config_dict[elem.attrib['name']] = self._get_property_value(elem)
            elif elem.tag == 'node':
                id = self._get_attribute_value(elem, 'id')
                if id in self.args.caida_config_dict["ASes"]:
                    logging.error("Duplicate AS id: %s", str(id))
                    sys.exit(1)
                node = {}
                for prop in elem:
                    if prop.tag == 'property':
                        node[prop.attrib['name']] = self._get_property_value(prop)
                self.args.caida_config_dict["ASes"][id] = node
                # create empty dict for assigned border routers
                self.assigned_br_per_as[id] = {}
            elif elem.tag == 'link':
                link = {}
                for prop in elem:
                    if prop.tag == 'property':
                        link[prop.attrib['name']] = self._get_property_value(prop)
                    else:
                        link[prop.tag] = self._get_property_value(prop)
                self.args.caida_config_dict["links"].append(link)

    def _get_property_value(self, prop):
        # check if attribute type is present
        if 'type' in prop.attrib:
            return self._get_casted_value(prop, 'type', lambda x: x.text)
        else:
            return prop.text
    
    def _get_attribute_value(self, elem, attr):
        # check if attribute is present
        if attr not in elem.attrib:
            return None
        # check if attribute type is present
        attr_type = attr + '.type'
        if attr_type in elem.attrib:
            return self._get_casted_value(elem, attr_type, lambda x: x.attrib[attr])
        else:
            return elem[attr]
        
    def _get_casted_value(self, elem, attr, val_f):
        if val_f(elem) is None:
            return None
        if elem.attrib[attr] == 'int':
            return int(val_f(elem))
        elif elem.attrib[attr] == 'float':
            return float(val_f(elem))
        elif elem.attrib[attr] == 'string':
            return str(val_f(elem))
        else:
            return val_f(elem)

    # def _reg_addr(self, topo_id: TopoID, elem_id, addr_type):
    #     subnet = self.args.subnet_gen[addr_type].register(str(topo_id))
    #     return subnet.register(elem_id)

    def _reg_link_addrs(self, local_br, remote_br, addr_type):
        link_name = str(sorted((local_br, remote_br)))
        subnet = self.args.subnet_gen[addr_type].register(link_name)
        return subnet.register(local_br), subnet.register(remote_br)

    def _iterate(self, f):
        for as_id, as_conf in self.args.caida_config_dict["ASes"].items():
            f(as_id, as_conf)

    def generate(self):
        self._read_links()
        # in a first step we allocate all networks, so that we can later use
        # the IPs in the generate functions.
        self._iterate(self._register_addrs)
        networks = {}
        for k, v in self.args.subnet_gen[ADDR_TYPE_4].alloc_subnets().items():
            networks[k] = v
        for k, v in self.args.subnet_gen[ADDR_TYPE_6].alloc_subnets().items():
            networks[k] = v
        self._iterate(self._generate_as_topo)
        return self.caida_dicts, networks

    def _register_addrs(self, as_id, as_conf):
        self._register_inter_as_br_entries(as_id, as_conf)
        self._register_intra_as_br_entries(as_id, as_conf)

    def _register_inter_as_br_entries(self, as_id, as_conf):
        addr_type = ADDR_TYPE_6 if self.args.ipv6 else ADDR_TYPE_4
        for (linkto, remote, attrs, l_br, r_br) in self.links[as_id]:
            self._register_br_entry(as_id, remote, 
                                    linkto, attrs, l_br, r_br, addr_type)
            
    def _register_intra_as_br_entries(self, as_id, as_conf):
        addr_type = ADDR_TYPE_6 if self.args.ipv6 else ADDR_TYPE_4
        # register all combinations of border routers
        for l_br, r_br in combinations(self.assigned_br_per_as[as_id], 2):
                self._register_br_entry(as_id, as_id, LinkRel.SIBLING, {}, 
                                        l_br, r_br, addr_type)
            

    def _register_br_entry(self, local, remote, remote_type, attrs,
                           local_br, remote_br, addr_type):
        link_addr_type = ADDR_TYPE_6 if self.args.ipv6 else ADDR_TYPE_4
        self._reg_link_addrs(local_br, remote_br, link_addr_type)

    def _br_name(self, as_id, lat, long, assigned_br_by_loc_per_as, br_ids):
        loc = (lat, long)
        if loc in assigned_br_by_loc_per_as[as_id]:
            # BR with multiple interfaces, reuse assigned id
            br_id = assigned_br_by_loc_per_as[as_id].get(loc)
            if br_id is None:
                # assign new id
                br_ids[as_id] += 1
                assigned_br_by_loc_per_as[as_id][loc] = br_id = br_ids[as_id]
        else:
            # BR with single interface
            br_ids[as_id] += 1
            br_id = br_ids[as_id]
            assigned_br_by_loc_per_as[as_id][loc] = br_id

        return "br%s_%d" % (str(as_id), br_id)
        

    def _read_links(self):
        if not self.args.caida_config_dict.get("links", None):
            return
        assigned_br_by_loc_per_as = defaultdict(lambda: defaultdict(int))
        br_ids = defaultdict(int)
        for attrs in self.args.caida_config_dict["links"]:
            as_from = attrs.get("from")
            as_to = attrs.get("to")
            linkto = LinkRel[attrs.get("rel").upper()]
            linkto_from = linkto_to = linkto
            if linkto == LinkRel.CUSTOMER:
                linkto_from = LinkRel.PROVIDER
                linkto_to = LinkRel.CUSTOMER
            lat = attrs.get("latitude")
            long = attrs.get("longitude")
            from_br = self._br_name(as_from, lat, long,
                                    assigned_br_by_loc_per_as, br_ids)
            to_br = self._br_name(as_to, lat, long,
                                  assigned_br_by_loc_per_as, br_ids)
            self.links[as_from].append((linkto_to, as_to, attrs, from_br, to_br))
            self.links[as_to].append((linkto_from, as_from, attrs, from_br, to_br))

            link_details = {
                    "capacity": attrs.get("capacity", None),
                }
            if from_br not in self.assigned_br_per_as[as_from]:
                self.assigned_br_per_as[as_from][from_br] = {
                    "latitude": lat,
                    "longitude": long,
                }
            self.assigned_br_per_as[as_from][from_br][to_br] = link_details

            if to_br not in self.assigned_br_per_as[as_to]:
                self.assigned_br_per_as[as_to][to_br] = {
                    "latitude": lat,
                    "longitude": long,
                }
            self.assigned_br_per_as[as_to][to_br][from_br] = link_details


    def _generate_as_topo(self, as_id, as_conf):
        self.caida_dicts[as_id] = self.args.caida_config_dict["ASes"][as_id]
        self.caida_dicts[as_id]["routers"] = self.assigned_br_per_as[as_id]
    
