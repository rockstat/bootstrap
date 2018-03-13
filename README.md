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

![Alcolytics sheme](https://alcolytics.ru/media/alco-scheme.png)

# Alcolytics Bootstrap

Ansible playbook для автоматической установки Alcolytics
Скрипт сделан для Ubuntu 16.04, на других работать не будет.

Подразумевается, что у вас уже имеется сервер под Alcolytics под управлением OC Ubuntu 16.04
и поддомен alco.yourdomain.ru (или какой-либо другой) указывет на этот сервер

# Установка

Требуется Ubuntu 16.04
Основаная система настройки это Ansible, но ей для работы нужны некоторые пакеты, которых нет в дефолтовой поставке.
Есть несколько путей.



## Установщик установщика 

Установка минимальных curl, если нет
```bash
sudo apt -y update && sudo apt -y install curl
```

Предконфигурация системы и получение свежей версии скрипта установки. Это скрипт из `bin/from-scratch`
```bash
sudo bash <(curl -Ss https://raw.githubusercontent.com/alcolytics/alco-bootstrap/master/bin/from-scratch)
```


Запуск установщика Alcolytics
```bash
ansible-playbook alcolytics.yml --connection=local
```

**Полная версия тут:** [alco.readme.io](https://alco.readme.io/docs/server-setup)

## Вопросы и общение

* Канал в telegram https://t.me/alcolytic
* Раздел поддержки в документации https://alco.readme.io/discuss

## License

This software is licensed under the MIT license. See [License File](LICENSE) for more information.

