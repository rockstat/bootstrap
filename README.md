# About Alcolytics

Is an open source platform for a web and product analytics. 
It consists of a set of components: JavaScript tracking client for web applications; 
server-side data collector; services for geo-coding and detecting client device type; 
a new server deployment system.
[Read more](https://alco.readme.io/docs)

Платформа для web и продуктовой аналитики с открытым исходным кодом.
Включает в себя JavaScript трекер для сайта; сервис получения, обогащения,
сохранения и стриминга данных; сервисы гео-кодинга и определения типа клиентского устройства;
систему развертывания нового сервера.
[Подробнее](https://alco.readme.io/docs) 

![Alcolytics sheme](https://raw.githubusercontent.com/alcolytics/alco-tracker/master/docs/alco-scheme.png)

# Alcolytics Bootstrap

Ansible playbook для автоматической установки Alcolytics
Скрипт сделан для Ubuntu 16.04, на других работать не будет.

Подразумевается, что у вас уже имеется сервер под Alcolytics под управлением OC Ubuntu 16.04
и поддомен alco.yourdomain.ru (или какой-либо другой) указывет на этот сервер

# Установка

Требуется Ubuntu 16.04
Основаная система настройки это Ansible, но ей для работы нужны некоторые пакеты, которых нет в дефолтовой поставке.
Есть несколько путей.

## С сервера

### Вариант 1: скрипт который все установит и сгенерит нужные файлы

Первым делом надо правдой или неправдой пробраться в консоль сервера. На MacOS это можно сделать в обычном териминале

    ssh root@superduper.me
    
В Win для этих целей есть програмка putty

После успешного проникновения на объет следует выполнить: 

    apt -y update && apt -y install curl && bash <(curl -Ss https://raw.githubusercontent.com/alcolytics/alco-bootstrap/master/bin/from-scratch)

И вуаля! Все необходимое установлено!

![Alcolytics sheme](https://raw.githubusercontent.com/alcolytics/alco-bootstrap/master/docs/setup_complete.png)

После этого скрипт продложит создать файл инвентаря, после останется только запустить основгной устанощик,
который сделает всю грязную работу по установке и настройке кучи необходимого софта

![Alcolytics sheme](https://raw.githubusercontent.com/alcolytics/alco-bootstrap/master/docs/success.png)

    
    ansible-playbook alco.yml --connection=local
    

### Вариант 2: я задрот или параноик или что-то пошло не так


Устновите минимальные необходимые зависимости и произведите преднастройку системы, последовательно выполнив все команды.

    sudo -i
    
    apt -y update
    
    apt install -y python-minimal python-pip python-netaddr git locales

    echo -e 'LANG=en_US.UTF-8\nLC_ALL=en_US.UTF-8' | sudo tee /etc/default/locale
    locale-gen en_US.UTF-8
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
    
    pip install ansible
    
    git clone https://github.com/alcolytics/alco-bootstrap

    cd ~/alco-bootstrap
    
Теперь надо создать файл inventory/private вот с таким содержимым:

    [private]
    alcostat ansible_host=alco.yourdomain.com
    
    [private:vars]
    tracker_domain=alco.yourdomain.com
    contact_email=youemail@example.com

После этого, можно запускать процесс установки    
    
    ansible-playbook alco.yml --connection=local


## Установка счетчика на сайт

Обращайтесь к докам AlcoJS:

* Репозиторий: https://github.com/alcolytics/alcojs
* Документации: https://alco.readme.io/docs/js-api
* Актуальный сниппет: https://github.com/alcolytics/alcojs/blob/master/snippet

## Кастомизация конфигурации

### Изсключение из гита

Монархически принято решение: свои файлы инвентаря следует именовать с префиксом priv, например `private`
дабы не разводить бадак в `.gitignore`.  

### Конфигурация системы

Полный список параметров можно найти в дефолтах ролей в `roles/*/defaults/*` 
Не изменяйтся основной файл `group_vars/all`, создайте отдельный файл совпадающий с названием группы хостов.
Пример: делаете копию `inventory/all` под названием `inventory/private`, создаете файл конфигурации `group_vars/private`,
все, указанные настройки перезапишут аналоги из `all`. 


## Обновление Alcolytics

Проект развивается очень быстро, обновления могут выходить часто, вплоть до нескольких раз в день. 
Обо всех важных или обязательных обновах можно узнать в телеге https://t.me/alcolytic

Процесс обновления повторяет установку:

    cd ~/alco-bootstrap
    git pull
    ansible-playbook alco.yml --connection=local


### Автоматическое централизованное обновление

Имеется централизованная система автоматического обновления всех серверов Alcolytics. Она пока не на том уровне развития,
чтобы прикрутить ее к личному кабинету (но скоро планируется). Для подключения достаточно найти в чате Dmitry Rodin (меня) и попросить 
добавить сервер в список доставки обновлений.

Скажу сразу, по дефолту предусмотрена функция удаленного обновления, для этого в проекте имеется
специальный ключ public_keys/alco.pub, при помощи которого сервер обновлений может подключатся к серверу Alcolytics 
для выполнения необходимых операция. Если вы не желаете иметь ничего общего с сервером обновлений, 
просто удалите этот файлик.


## Вопросы и общение

* Канал в telegram https://t.me/alcolytic
* Раздел поддержки в документации https://alco.readme.io/discuss

## License

This software is licensed under the MIT license. See [License File](LICENSE) for more information.

