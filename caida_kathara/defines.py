# Copyright 2015 ETH Zurich
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
:mod:`defines` --- Constants
============================
Contains constant definitions used throughout the codebase.
"""

#: Generated files directory
GEN_PATH = 'kathara_lab'
#: Default CAIDA file
DEFAULT_CAIDA_FILE = "default.xml"
#: Networks config
NETWORKS_FILE = "networks.conf"

# Default IPv4 network
DEFAULT_NETWORK = "10.0.0.0/8"
DEFAULT_PRIV_NETWORK = "192.168.0.0/16"
DEFAULT_SCN_DC_NETWORK = "172.20.0.0/20"

# Default IPv6 network, our equivalent to 127.0.0.0/8
# https://en.wikipedia.org/wiki/Unique_local_address#Definition
DEFAULT6_MASK = "/104"
DEFAULT6_NETWORK_ADDR = "fd00:f00d:cafe::7f00:0000"
DEFAULT6_NETWORK = DEFAULT6_NETWORK_ADDR + DEFAULT6_MASK
DEFAULT6_PRIV_NETWORK_ADDR = "fd00:f00d:cafe::c000:0000"
DEFAULT6_PRIV_NETWORK = DEFAULT6_PRIV_NETWORK_ADDR + DEFAULT6_MASK
DEFAULT6_CLIENT = "fd00:f00d:cafe::7f00:0002"
DEFAULT6_SERVER = "fd00:f00d:cafe::7f00:0003"
