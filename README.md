# Ansible playbook for deploy Rockstat platform

## Rockstat architecture

![Rockstat sheme](https://rockstat.ru/media/rockstat_v3_arch.png?3)

[Read more](https://rockstat.ru/about)

## Caution!

Don't install rockstat on existing server with other software! 
Setup process do significant system reconfiguration and can kill others.


## Requirements

Cloud or dedicated server with at least:

- 2 cores
- 8 gb mem
- 60 gb ssd (depends on your data amount)

OS must be Ubutnu 16.04, moreover you should prepare domain name for platform

### Domain records

Typically DNS zone looks like this:

```
stats.yourdomain.ru    A  SERVER.IP
*.stats.yourdomain.ru  A  SERVER.IP
```

for second level domains:

```
@                      A  SERVER.IP
*.yourdomain.ru        A  SERVER.IP
```

### Setup / upgrade / reconfigure

Once you should setup curl for get install script from repository.

```bash
sudo apt -qqy update && sudo apt -qqy install curl
```

Next times you can just execute setup manager using:

```bash
sudo bash -c 'bash <(curl -Ss https://raw.githubusercontent.com/rockstat/bootstrap/dev/bin/loader)'
```

Then follow instructions. Platform will be installed to `/srv/platform`


## Take a power implicit using Ansible 


### Setup internal OpenVPN server


## Configuration details

Create configuration for your hosts group `groupvars/private.yml`
You can override configuration by specifing alternative values.

### IPv6

By default setup tool disabling IPv6 support.
To prevent set `disable_ipv6` to `no` at you custom config.

## Extending bootstrap configuration



### Anaconda/Jupyter additional packages


```yaml
---
jup_with_conda:
  - ujson
jup_with_pip:
  - prodict
```

### Os params (dirty drarft)

redis requirements

    net.core.netdev_budget = 300 
    net.core.netdev_max_backlog = 3000
    sysctl -w net.ipv4.tcp_sack=0
    sysctl -w net.ipv4.tcp_fin_timeout=20
    sysctl -w net.ipv4.ip_local_port_range='20000 60000'


    echo never > /sys/kernel/mm/transparent_hugepage/enabled

## Community

Join to discuss with other users

* Telegram https://t.me/rockstats
* Facebook https://fb.com/rockstatX

## Rockstat Bootstrap License and Authors

* Author:: Dmitry Rodin <madiedinro@gmail.com>
* Author:: Ivan Golubenko <fedorsymkin52@gmail.com>
* Maintainer:: Alexander Shvets <ashwets@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
