# Ansible playbook for deploy Rockstat platform

## About Rockstat

Is an open source platform for a web and product analytics. 
It consists of a set of components: JavaScript tracking client for web applications; 
server-side data collector; services for geo-coding and detecting client device type; 
a new server deployment system.
[Read more](https://rockstat.ru/about)

![Rockstat sheme](https://rockstat.ru/media/rockstat_v3_arch.png?3)

## Установка

Скрипт сделан для Ubuntu 16.04, на других работать не будет.
Подразумевается, что у вас уже имеется сервер под управлением OC Ubuntu 16.04

### Домен

Треуется настроить DNS следующим образом 

stats.yourdomain.ru    A  ВАШ СЕВЕРВЕР
*.stats.yourdomain.ru  A  ВАШ СЕВЕРВЕР

### Установка

Устанговка самых необходимых пакетов (если нет)

```bash
sudo apt -y update && sudo apt -y install curl
```

Запуск установщика

```bash
bash <(curl -Ss https://raw.githubusercontent.com/rockstat/bootstrap/dev/bin/runner)

cd /srv/platform/bootstrap/

```

Запуск Rockstat playbook

```bash


cd /srv/platform/bootstrap

ansible-playbook platform.yml --connection=local
```


### Новый устаношик

python2 bin/installer.py



### Migrating from submodules to ansible-galaxy

First install deps

    ansible-galaxy install -r install_roles.yml

To remove submodules

    git submodule deinit --all --force
    git rm --cached roles/dr*
    git rm --cached roles/jdauphant.nginx -r
    rm -f .gitmodules
    rm -rf .git/modules
    rm -rf roles/dr*
    rm -rf roles/jdauphant.nginx



## Полезное

### Генерация пароля httpasswd

```
NEW_USER=dr
printf "$NEW_USER:`openssl passwd -apr1`\n"
```
### Os params

for redis

    echo never > /sys/kernel/mm/transparent_hugepage/enabled

## Вопросы и общение

* Telegram https://t.me/rockstats
* Facebook https://fb.com/rockstatX

## License and Authors

* Author:: Dmitry Rodin <madiedinro@gmail.com>
* Author:: Ivan Golubenko <fedorsymkin52@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
