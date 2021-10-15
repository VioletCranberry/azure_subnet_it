from azure.common.client_factory import get_azure_cli_credentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import HttpResponseError
from tabulate import tabulate
from netaddr import IPSet
import argparse
import logging
import sys


class AzureClients:
    def __init__(self, subscription_id):
        self.subscription_id = subscription_id

        self._resource_client = None
        self._network_client = None

        self.credential = get_azure_cli_credentials()[0]

    @property
    def resource_client(self):
        if not self._resource_client:
            try:
                client = ResourceManagementClient(
                    self.credential,
                    self.subscription_id)
                return client
            except HttpResponseError as error:
                logging.fatal(f"Encountered error: {error}")
                sys.exit(1)

    @property
    def network_client(self):
        if not self._network_client:
            try:
                client = NetworkManagementClient(
                    self.credential,
                    self.subscription_id)
                return client
            except HttpResponseError as error:
                logging.fatal(f"Encountered error: {error}")
                sys.exit(1)


class ResourceGroupResourcesInfo(AzureClients):
    def __init__(self, subscription_id, rg_name):
        self.rg_name = rg_name

        super().__init__(subscription_id)
        self.resources_list = super().resource_client.resources.list_by_resource_group(self.rg_name)

        self.resources = [resource.type for resource in list(self.resources_list)]
        self.has_networks = self.has_networks(self.resources)

        if not self.has_networks:
            logging.info(f"Skipping [{self.rg_name}]: no VNets found!")

    @staticmethod
    def has_networks(resources):
        if 'Microsoft.Network/virtualNetworks' not in resources:
            return False
        return True


class ResourceGroupVnetInfo(AzureClients):
    def __init__(self, subscription_id, rg_name):
        self.rg_name = rg_name
        self.vnet_info = {}

        super().__init__(subscription_id)
        self.vnet_list = super().network_client.virtual_networks.list(self.rg_name)

        for vnet in self.vnet_list:
            logging.info(f"[{self.rg_name}]: VNet [{vnet.name}]")

            network_data = self.get_network_data(vnet)
            network_data.update(
                self.get_subnet_data(vnet))
            self.vnet_info.update(network_data)

    @staticmethod
    def get_subnet_data(vnet):
        return {
            'subnet_names': [subnet.name for subnet in vnet.subnets],
            'reserved_ips': [subnet.address_prefix for subnet in vnet.subnets]
        }

    @staticmethod
    def get_network_data(vnet):
        ip_addr_space = vnet.address_space.address_prefixes

        ips_available = IPSet(ip_addr_space) ^ IPSet([subnet.address_prefix for subnet in vnet.subnets])
        cidrs_available = [str(cidr) for cidr in ips_available.iter_cidrs()]

        return {
            'vnet_name': [vnet.name],
            'address_space': ip_addr_space,
            'available': cidrs_available
        }


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--subscription_id',
                        action='store',
                        type=str,
                        required=True)
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        required=False)
    parser.add_argument('-f', '--format',
                        action='store_true',
                        required=False)
    return parser.parse_args()


def resource_group_net_data(subscription_id, resource_group_name):
    logging.info(f"Checking Resource Group [{resource_group_name}]")

    data = None
    resources = ResourceGroupResourcesInfo(
        subscription_id, resource_group_name)

    if resources.has_networks:
        data = ResourceGroupVnetInfo(
            subscription_id,
            resource_group_name)

    return data.vnet_info if data else None


def main():
    args = get_arguments()

    logger = logging.getLogger("azure")
    logger.setLevel(logging.ERROR)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s - %(module)5s: "
                               "%(levelname)s - %(message)s")

    azure_clients = AzureClients(
        args.subscription_id)

    resource_groups = azure_clients.resource_client.resource_groups.list()
    for group in list(resource_groups):

        net_data = resource_group_net_data(
            args.subscription_id, group.name)
        if net_data:

            if args.format:
                print(tabulate(net_data,
                               headers=["Virtual Network",
                                        "Address Space",
                                        "Available Ranges",
                                        "Reserved Subnets",
                                        "Reserved Ranges"
                                        ], tablefmt="pretty"))
            else:

                logging.info(f"Address Space: "
                             f"{net_data.get('address_space')}")
                logging.info(f"Available Ranges: "
                             f"{net_data.get('available')}")
                logging.info(f"Reserved Subnets: "
                             f"{net_data.get('subnet_names')}")
                logging.info(f"Reserved Ranges: "
                             f"{net_data.get('reserved_ips')}")


if __name__ == "__main__":
    main()
