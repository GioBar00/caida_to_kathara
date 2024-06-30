"""
:mod:`caida_to_kathara` --- Kathara lab generator from Caida topology
=============================================
"""
# Stdlib
import argparse

from caida_kathara.defines import (
    GEN_PATH,
    DEFAULT_NETWORK,
    DEFAULT6_NETWORK,
    DEFAULT_CAIDA_FILE,
)
from caida_kathara.config import (
    ConfigGenerator,
    ConfigGenArgs,
)


def add_arguments(parser):
    parser.add_argument('-c', '--caida-config', default=DEFAULT_CAIDA_FILE,
                        help='Path policy file')
    parser.add_argument('-n', '--network', default=DEFAULT_NETWORK,
                        help='IPv4 network to create subnets in (E.g. "127.0.0.0/8"')
    parser.add_argument('-n6', '--network-v6', default=DEFAULT6_NETWORK,
                        help='IPv6 network to create subnets in (E.g. "fd00:f00d:cafe::7f00:0000/104"')
    parser.add_argument('-v6', '--ipv6', action='store_true',
                        help='Use IPv6')
    parser.add_argument('-o', '--output-dir', default=GEN_PATH,
                        help='Output directory')
    parser.add_argument('--docker-registry', help='Specify docker registry to pull images from')
    parser.add_argument('--image-tag', default='latest', help='Docker image tag')
    return parser


def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = ConfigGenArgs(parser.parse_args())
    confgen = ConfigGenerator(args)
    confgen.generate_all()


if __name__ == "__main__":
    main()
