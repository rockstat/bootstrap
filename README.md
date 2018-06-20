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
```

Запуск установщика

```bash
sudo apt -qqy update && sudo apt -qqy install curl && bash <(curl -Ss https://raw.githubusercontent.com/rockstat/bootstrap/dev/bin/loader)
```

Установка будет произведена в `/srv/platform`


### Новый устаношик

python2 bin/installer.py


## Полезное

### Os params

redis requirements

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
