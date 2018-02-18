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

Устновите минимальные необходимые зависимости

    apt -y update && apt install -y python-minimal python-pip python-netaddr git locales
    
    pip install ansible
    
Если возникает ошибка связанная с локалью, установите локаль и запустите еще раз
        
    echo -e 'LANG=en_US.UTF-8\nLC_ALL=en_US.UTF-8' | sudo tee /etc/default/locale
    locale-gen en_US.UTF-8
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
    
Загрузка и запуск скрипта установки
    
    # dev git clone git@github.com:madiedinro/alco-boostrap.git
    git clone https://github.com/madiedinro/alco-boostrap.git
    cd alco-boostrap
    
Ниже есть блок поо создание файла инвентаря, сделайте это. 
Запуск процесса установки
    
    ansible-playbook alco-server.yml --connection=local
    
    ansible-playbook alco-platform.yml --connection=local

## С другого компьюетра

Установите ansible и python-netaddr при помощи используемого менеджера пакетов.
Ниже есть блок поо создание файла инвентаря, сделайте это.    

Запуск процесса установки. Если вход по паролю, добавьте ` --ask-pass`
    
    ansible-playbook alco-server-initial.yml
    
Если запускаете первый раз, то добавьте `-u <дефолтовый пользователь на сервере>`
    
    ansible-playbook alco-server.yml
    
    ansible-playbook alco-platform.yml

## Создание файла инвентаря

Создайте файл `inventory/all`

    [alcogroup]
    alcostat ansible_host=<домен трекера> initial_user=root
    
    
    [alcogroup:vars]
    mixpanel_token=<токен mixpanel, если есть>
    tracker_domain=<домен трекера>
    contact_email=<контактная почта>
    
    
    [alco:children]
    alcogroup
    
    
    [alco:vars]
    
    # Ключ от сервиса mailgun. Если поставить, на почту придут все данные
    mailgun_api_key:
    # Что-то вроде "Alcolytics Setup <hello@alcolytics.ru>" но на своем домене
    alco_email_from_custom: <почта с домена в mailgun>
    
Помимо этого сгенерируйте SSH ключ и положите его публичную часть в public_keys/alco.pub
    
    
## Вопросы и общение

* Канал в telegram https://t.me/alcolytic
* Раздел поддержки в документации https://alco.readme.io/discuss

## License

This software is licensed under the MIT license. See [License File](LICENSE) for more information.

