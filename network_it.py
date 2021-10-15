from subnet_it import AzureClients
from subnet_it import resource_group_net_data
from netaddr import IPSet, IPNetwork
from tabulate import tabulate
import argparse
import logging


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--subscription_id',
                        action='store',
                        type=str,
                        required=True)
    parser.add_argument('-a', '--address_space',
                        action='store',
                        type=str,
                        required=True)
    parser.add_argument('--size',
                        action='store',
                        type=int,
                        required=True)
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        required=False)
    parser.add_argument('-f', '--format',
                        action='store_true',
                        required=False)
    return parser.parse_args()


def get_network_data(vnet_space, address_space, mask):
    free_subnets = []

    available_range = IPSet([address_space]) ^ IPSet(vnet_space)
    available_cidrs = [str(cidr) for cidr in available_range.iter_cidrs()]

    for cidr in available_cidrs:
        network = IPNetwork(cidr)
        subnets = list(network.subnet(mask))
        free_subnets.extend(list(subnets))

    return {
        'available_ranges': available_cidrs,
        'available_subnets': free_subnets,
        'reserved_ranges': vnet_space
    }


def main():
    args = get_arguments()

    logger = logging.getLogger("azure")
    logger.setLevel(logging.ERROR)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s - %(module)5s: "
                               "%(levelname)s - %(message)s")

    azure_clients = AzureClients(
        args.subscription_id)

    vnet_address_spaces = []
    vnet_names = []

    resource_groups = azure_clients.resource_client.resource_groups.list()
    for group in list(resource_groups):

        net_data = resource_group_net_data(args.subscription_id, group.name)
        if net_data:

            vnet_address_spaces.append(",".join([
                space for space in net_data.get('address_space')]
            ))
            vnet_names.extend(net_data.get('vnet_name'))

    net_data = get_network_data(vnet_address_spaces, args.address_space, args.size)
    net_data.update({'vnet_names': vnet_names})

    if args.format:
        print(tabulate(net_data,
                       headers=["Free range",
                                "Available Subnets",
                                "Reserved Ranges",
                                "Virtual Network"
                                ], tablefmt="pretty"))

    else:

        logging.info(f"Free range: "
                     f"{net_data.get('available_ranges')}")
        logging.info(f"Available Subnets: "
                     f"{net_data.get('available_subnets')}")
        logging.info(f"Reserved Ranges: "
                     f"{net_data.get('reserved_ranges')}")
        logging.info(f"Virtual Network: "
                     f"{net_data.get('vnet_names')}")


if __name__ == "__main__":
    main()
