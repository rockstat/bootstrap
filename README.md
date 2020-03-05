# Rockstat bootstrap

![Rockstat architecture](https://rstat.org/static/media/schemas/rockstat-main-components.svg?3)

[Read more](https://rstat.org)

## Requirements

Virtual or dedicated server with at least:

- 2 core
- 8 Gb mem
- 60 Gb SSD

Requires OS: Ubutnu 16.04.x

**Caution!**

Rockstat required fresh server without any other software. Don't  install rockstat on existing server with other software! 
Setup process do significant system reconfiguration.

### Domain records


Typically DNS zone looks like:

```
stats.yourdomain        A  1.2.3.4
*.stats.yourdomain      A  1.2.3.4
```

for second level domains:

```
yourdomain (or @)       A  1.2.3.4
*.yourdomain            A  1.2.3.4
```

### Start server

Required steps depends of 

### Local setup on server

#### Connect to server

Open Terminal application (On Windows know as `cmd`)  Type following connection command:

```shell
ssh root@yourdomain
```

#### Intials

You need to setup curl only once

```shell
sudo apt -qqy update && sudo apt -qqy install curl
```

Then run:

```shell
curl -s "https://raw.githubusercontent.com/rockstat/bootstrap/master/bin/kickstart?$(date '+%s')" | sudo -E bash -

sudo reboot
```

For **development** version

```shell
curl -s "https://raw.githubusercontent.com/rockstat/bootstrap/dev/bin/kickstart?$(date '+%s')" | sudo -E BRANCH=dev bash -
sudo reboot
```

 #### Upgrade / reconfigure installation

Rockstat is on active development stage. Lookat at page [What's new](https://rock.st/docs/what-s-new). Take a latest version.

To run setup tool just type `rockstat`

### Direct ansible usage

configure inventory

```
# ...
test ansible_host=test.rstat.org realname=User email=hello@rstat.org
```
Generate password using `make password`. Execute playbook

```
 AHOST=test
 APASS='$apr1$G2B2.GYy$QiBhuOZeRC03moZTPsB561'
ansible-playbook platform.yml --limit=$AHOST --tags=ssl,full -e admin_password=$APASS
```

#### Custom tasks

You should create `tasks/custom.yml`. Possible to be an empty file.

```shell
touch tasks/custom.yml
```

## Params

To force SSL `-e ssl_force=1`

## Overriding configuration

Create configuration for your hosts group `group_vars/private.yml`
You can override configuration by specifing alternative values.

Configurations has a parts prepared for easy overriding/extending:

#### images_extra

```yaml
_images_extra:
  chproxy: myusername/chproxy
  redis: redis:4-alpine
```

will override only thease two images

#### Custom env

```yaml
_containers_env_extra:
  director:
    PORT: 1899
```

#### Disable support access

```yaml
enable_support: no
```

### Google Cloud Compute Engine instance configuration

You need to configure additional persistent SSD disk.

Use docs at https://cloud.google.com/compute/docs/disks/add-persistent-disk

Or execute prepared script that configure `/dev/sdb` disk. **Danger! If disk currently not mounted it will be formatted!**

```
curl -s https://raw.githubusercontent.com/rockstat/bootstrap/master/bin/gcloud_sdb | sudo bash -
```

### Yandex Cloud instance configuration

Prepating additional drive

Or execute prepared script that configure `/dev/vdb` disk. **Danger! If disk currently not mounted it will be formatted!**

```
curl -s https://raw.githubusercontent.com/rockstat/bootstrap/master/bin/ycloud_vdb | sudo bash -
```


### IPv6

By default setup tool disabling IPv6 support.
To prevent set `disable_ipv6` to `no` at you custom config.

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
