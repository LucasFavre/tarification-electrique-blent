import os
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow.decorators import dag, task
from airflow.operators.python_operator import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.models import Connection
from airflow import settings

import requests


def create_conn(conn_id, conn_type, host, login, password, schema, port):
    """
    Check s'il y a une connection à la base de données déjà existante dans Airflow, et la crée sinon.

    """
    conn = Connection(conn_id=conn_id,
                      conn_type=conn_type,
                      host=host,
                      login=login,
                      password=password,
                      schema=schema,
                      port=port)
    session = settings.Session()
    conn_name = session.query(Connection).filter(Connection.conn_id == conn.conn_id).first()

    if str(conn_name) == str(conn.conn_id):
        return None

    session.add(conn)
    session.commit()
    return conn


DAG_NAME = os.path.basename(__file__).replace(".py", "") 


default_args = {
    'owner': 'blent',
    'retries': 1,
    'retry_delay': timedelta(seconds=10),
    'email_on_failure': True,
    'email': ['youremail@blent.ai'],
    'email_on_retry': False
}


def get_conso(**kwargs):

    thirtydays_ago = (datetime.strptime(kwargs['date'], '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    params = {'select' : ['code_insee_region', 'AVG(consommation)*4 as consommation_moyenne_kwh'], 
    'where' : f'date_heure >= "{thirtydays_ago}"',
    'group_by' : 'code_insee_region', 'limit' : 50}
    result = requests.get("https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-regional-tr/records", params = params)

    data = [(int(region['code_insee_region']), round(region['consommation_moyenne_kwh'], 2)) for region in result.json()['results']]
    data_string = ', '.join(f"({x}, {y})" for x, y in data)

    print(data_string)

    ti = kwargs['ti']
    ti.xcom_push(key='sql_values', value = data_string)
    

@dag(DAG_NAME, default_args=default_args, schedule_interval="@daily", start_date=days_ago(1))
def dag_update_conso_regions():
    """
    Ce DAG récupère tous les jours les consommations moyennes des 30 derniers jours pour chaque région,
    afin de mettre à jour la BDD Postgres.
    """

    conn_id = 'my_postgres_connection'

    host = '34.38.55.102'

    create_conn(
        conn_id=conn_id,
        conn_type='postgres',
        host=host,
        login='blent',
        password='blent',
        schema='tarification-blent',
        port=5432
    )


    table_name = 'conso_moyenne_30jours'

    insert_sql_template = f"""
    INSERT INTO {table_name}
    VALUES 
    """

    delete_sql = f'DELETE FROM {table_name};'


    @task()
    def show_date(**kwargs):
        print("La date d'exécution est : {}".format(kwargs["date"]))


    task_show_date = show_date(date="{{ ds }}")
    task_get_conso = PythonOperator(
        task_id='task_get_conso',
        python_callable=get_conso,
        provide_context=True,
        op_kwargs={'date' : "{{ ds }}"}
    )
    task_delete_data = PostgresOperator(
        task_id='task_delete_data',
        postgres_conn_id=conn_id, 
        sql=delete_sql,
    )
    task_insert_data = PostgresOperator(
        task_id='task_insert_data',
        postgres_conn_id=conn_id,
        sql=insert_sql_template + "{{ ti.xcom_pull(task_ids='task_get_conso', key = 'sql_values') }}"
    )
    
   
    task_show_date.set_downstream(task_get_conso)  # date -> get_conso
    task_get_conso.set_downstream(task_delete_data) # get_conso -> delete_data
    task_delete_data.set_downstream(task_insert_data) # delete_date -> insert_data

dag_update_conso_regions_instance = dag_update_conso_regions()