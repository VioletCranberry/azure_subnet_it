# subnet_it

Dynamically calculate available for further subnetting free CIDRs based on already reserved subnets/ranges and Virtual Network address spaces.

Example:
```
❯ python subnet_it.py
usage: subnet_it.py [-h] -s SUBSCRIPTION_ID [-v] [-f]
subnet_it.py: error: the following arguments are required: -s/--subscription_id

python subnet_it.py -s '< subscription id >' -f
...
2021-06-10 15:08:19,508 - subnet_it: INFO - Checking Resource Group [rg_group_name]
2021-06-10 15:08:20,183 - subnet_it: INFO - [rg_group_name]: VNet [vnet_name]
+---------------+------------------+---------------------------------+-----------------+
| Address Space | Available Ranges |        Reserved Subnets         | Reserved Ranges |
+---------------+------------------+---------------------------------+-----------------+
| 10.15.0.0/16  |   10.15.0.0/23   |             test                |  10.15.5.0/27   |
|               |   10.15.2.0/24   |             test                |  10.15.20.0/24  |
...
+---------------+------------------+---------------------------------+-----------------+
...
```

TODO:
- Resource group/Vnet as arguments
- State file? (track the changes)
- Clean up requirements
- Documentation

# network_it

Dynamically calculate available for further subnetting free CIDRs based on already reserved subnets/ranges, Virtual Network address spaces, provided address space and expected size.

Example:
```
❯ python network_it.py -s '< subscription id >' -a '10.0.0.0/12' --size 22 -f
...
+-------------+-------------------+-----------------+--------------------------+
| Free range  | Available Subnets | Reserved Ranges |     Virtual Network      |
+-------------+-------------------+-----------------+--------------------------+
| 10.8.0.0/13 |    10.8.0.0/22    |   10.0.0.0/13   |         test             |
|             |    10.8.4.0/22    |                 |                          |
|             |    10.8.8.0/22    |                 |                          |
|             |   10.8.12.0/22    |                 |                          |
|             |   10.8.16.0/22    |                 |                          |
...
```

TODO:
- validation
- Documentation
- Print limit (currently outputs all)
