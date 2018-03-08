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

Установка производится либо с самого сервера либо с другого компьютера.

## С сервера

Требуется Ubuntu 16.04
Основаная система настройки это Ansible, но ей для работы нужны некоторые пакеты, которых нет в дефолтовой поставке.
Есть несколько путей.

### Вариант 1: скрипт который все установит и сгенерит нужные файлы

Запустить 

    apt -y install curl && bash <(curl -Ss https://raw.githubusercontent.com/alcolytics/alco-bootstrap/master/bin/from-scratch)


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


## Вопросы и общение

* Канал в telegram https://t.me/alcolytic
* Раздел поддержки в документации https://alco.readme.io/discuss

## License

This software is licensed under the MIT license. See [License File](LICENSE) for more information.

