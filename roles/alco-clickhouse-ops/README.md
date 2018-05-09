
from config


    # ClickHouse Migrations
    ch_path: '{{alco_tracker_path}}/clickhouse_schema'
    ch_operations:
    #  # Чистый SQL запрос
    #  - type: query
    #    query: 'SELECT count() FROM events'
    #
    # Миграция из локального файла
    #  - type: local_migration
    #    file: 2-migration-ren-table.yml
    #   Таблица с миграций
    - type: query_file
        file: '{{ch_path}}/table_migrations.sql'
    #   Файл миграции в репе трекера
    - type: migration
        file: '{{ch_path}}/2-migration-ren-table.yml'
    ##
    ##  - type: query_file
    ##    file: '{{ch_path}}/table_migrations.sql'

