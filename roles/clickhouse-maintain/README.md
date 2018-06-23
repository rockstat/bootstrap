
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



from playbook 



    # - include_role:
    #     name: alco-clickhouse-ops
    #   vars:
    #     alco_ch_ops_list: '{{ch_operations|default([]) + ch_operations_custom|default([])}}'
    #     alco_ch_ops_host: '127.0.0.1'
    #     alco_ch_ops_db: '{{alco_db_name}}'
    #   tags: ['schema']
