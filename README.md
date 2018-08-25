# Rockstat bootstrap

## Rockstat architecture

![Rockstat architecture](https://rstat.org/static/media/schemas/rockstat-main-components.svg?2)

[Read more](https://rstat.org)

## Caution!

Don't install rockstat on existing server with other software! 
Setup process do significant system reconfiguration and can kill others.


## Requirements

Virtual or dedicated server with at least:

- 2 core
- 8 Gb mem
- 60 Gb SSD

Requires OS: Ubutnu 16.04.x

### Domain records

Typically DNS zone looks like this:

```
stats.yourdomain.ru    A  SE.RV.ER.IP
*.stats.yourdomain.ru  A  SE.RV.ER.IP
```

for second level domains:

```
@                      A  SE.RV.ER.IP
*.yourdomain.ru        A  SE.RV.ER.IP
```

### Setup / upgrade / reconfigure

Setup curl once

```bash
sudo apt -qqy update && sudo apt -qqy install curl
```

Execute Rockstat management tool

```bash
curl -s https://raw.githubusercontent.com/rockstat/bootstrap/master/bin/kickstart | sudo -E bash -
```

From this moment you able to start management tool just type `rockstat` in command line


## Take a power using Ansible implicit


### Setup internal OpenVPN server


## Configuration details

Create configuration for your hosts group `groupvars/private.yml`
You can override configuration by specifing alternative values.

### IPv6

By default setup tool disabling IPv6 support.
To prevent set `disable_ipv6` to `no` at you custom config.


### PWD gen

    # python -c 'import crypt; print crypt.crypt("This is my Password", "$1$SomeSalt$")'

or using bash

run prepared script and follow instruction
 
```bash
./bin/make_creds
```


```bash
username=YOUR USER NAME; printf "${username}:`openssl passwd -apr1 ${password}`\n"
```

### Os params (dirty drarft)

redis requirements

    net.core.netdev_budget = 300 
    net.core.netdev_max_backlog = 3000
    sysctl -w net.ipv4.tcp_sack=0
    sysctl -w net.ipv4.tcp_fin_timeout=20
    sysctl -w net.ipv4.ip_local_port_range='20000 60000'

    echo never > /sys/kernel/mm/transparent_hugepage/enabled

## Special cases

### 2nd server on same domain

on 1st server configure configure frontier extra location for 2nd server (/v3) for example

```yaml
_nginx_frontier_extra:
  - location /v3 {
      proxy_redirect   off;
      proxy_http_version 1.1;
      proxy_set_header X-Real-IP       $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_cookie_domain new_server_domain current_server_domain;
      proxy_set_header Host      strip.rstat.org;
      proxy_redirect default;
      proxy_pass       https://new_server_domain:443/;
    }
```

on 2nd server configure nginx params. Add to `group_vars/private` 

```yaml
_nginx_proxy_params_extra:
  - set_real_ip_from  92.53.78.198
  - real_ip_header    X-Forwarded-For
  - real_ip_recursive on
```

### Run your own ACME DNS sever

Configure using config.cfg template, then run


   -p 172.16.25.1:53:53/udp -p 172.16.25.1:19980:19980 -p 172.16.25.1:19943:19943 \
```
docker run --rm --name acmedns \
   -p 53:53/udp -p 19980:19980 -p 19943:19943 \
   -v /srv/acme-dns/config:/etc/acme-dns:ro \
   -v /srv/acme-dns/data:/var/lib/acme-dns \
   --network=host \
   -d acme-dns
```

registering

```
curl -X POST http://auth.example.com/register
```

requesting 

```
docker run --rm \
  -e ACMEDNS_UPDATE_URL="http://auth....io/update" \
  -e ACMEDNS_USERNAME="..." \
  -e ACMEDNS_PASSWORD="..." \
  -e ACMEDNS_SUBDOMAIN="..." \
  acmesh --issue -d dimain.org  -d '*.domain.org' --dns dns_acmedns --log
```

```
docker run --rm acmesh --install-cert -d example.com \
--cert-file      /path/to/certfile/in/apache/cert.pem  \
--key-file       /path/to/keyfile/in/apache/key.pem  \
--fullchain-file /path/to/fullchain/certfile/apache/fullchain.pem \
```

### Referense

#### SSL certificates location

**default letsencrypt cert location**

ssl_certificate_key /etc/letsencrypt/live/srv.digitalgod.me/privkey.pem;
ssl_certificate     /etc/letsencrypt/live/srv.digitalgod.me/fullchain.pem;
ssl_trusted_certificate /etc/letsencrypt/live/srv.digitalgod.me/chain.pem;

**location when copy from asme.sh**
ssl_certificate_key     /etc/nginx/certs/{{domain}}/{{domain}}.key
ssl_certificate         /etc/nginx/certs/{{domain}}/fullchain.cer
ssl_trusted_certificate /etc/nginx/certs/{{domain}}/{{domain}}.cer

## Community

Join to discuss with other users

* Telegram https://t.me/rockstats
* Facebook https://fb.com/rockstatX

## Rockstat Bootstrap License and Authors

* Author:: Dmitry Rodin <madiedinro@gmail.com>
* Maintainer:: Ivan Golubenko <fedorsymkin52@gmail.com>
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
