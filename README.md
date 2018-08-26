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

### Setup / upgrade / reconfigure

You neet to setup curl only once

```bash
sudo apt -qqy update && sudo apt -qqy install curl
```

First-time setup tool execution

```bash
curl -s https://raw.githubusercontent.com/rockstat/bootstrap/master/bin/kickstart | sudo -E bash -
```

Next times availavale helpful short alias

```
rockstat
```

## Configuration details

Create configuration for your hosts group `groupvars/private.yml`
You can override configuration by specifing alternative values.

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
