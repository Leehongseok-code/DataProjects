
# Airflow DAGに関連する必須ライブラリのインポート
from airflow import DAG
from airflow.operators.python import PythonOperator

from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime, timedelta
import sys
import os

# codesディレクトリをPythonパスに追加してカスタムモジュールをインポートできるようにする
sys.path.append('/Users/hongseoklee/VSCodeWorkspace/MapleAnalysis/')

from codes.collect_rank_data import *

＃DAGのデフォルト設定値の定義
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

#DAGオブジェクトの作成
dag = DAG(
    'maplestory_rank_collection', 
    default_args=default_args, 
    description='Collect MapleStory rank data daily and update BigQuery',
    schedule='5 4 * * *', 
    catchup=False,
    tags=['maplestory', 'data_collection']
)

def collect_data_wrapper(**context):
    """
メープルストーリーランキングデータ収集のためのラッパー関数    
    """
    try:
        main()  # 実データ収集関数の実行
        return "Data collection completed successfully"
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

# PythonOperatorを使用したデータ収集ジョブの定義

collect_rank_data = PythonOperator(
    task_id='collect_rank_data',
    python_callable=collect_data_wrapper,
    dag=dag,
)

# BigQuery クエリ実行ジョブの定義
bigquery_task = BigQueryInsertJobOperator(
    task_id='run_bigquery_query',
    project_id='gameanalysis-440113',  # GCP 프로젝트 ID
    location='US',  # BigQuery 데이터셋 위치 (예: US, EU)
    configuration={
        "query": {
            "query": """
                CREATE OR REPLACE VIEW `gameanalysis-440113.maplestory_data.exp_diff_view` AS

                -- ユーザーが保持するかどうかを示す列を追加し、連続接続日を計算するクエリ
                WITH daily_exp AS (
                SELECT
                    date,
                    character_name,
                    MAX(character_exp) AS character_exp,
                    MAX(character_level) AS character_level
                FROM
                    `gameanalysis-440113.maplestory_data.NovaRankTable`
                GROUP BY
                    date, character_name
                ),

                exp_diff_data AS (
                SELECT
                    date,
                    character_name,
                    character_level,
                    character_exp,
                    LAG(character_exp) OVER (PARTITION BY character_name ORDER BY date) AS character_exp_prev,
                    character_exp - LAG(character_exp) OVER (PARTITION BY character_name ORDER BY date) AS exp_diff
                FROM
                    daily_exp
                ),

                access_data AS (
                SELECT
                    *,
                    exp_diff != 0 AS is_access
                FROM
                    exp_diff_data
                ),

                retention_data AS (
                SELECT
                    *,
                    LAG(is_access) OVER (PARTITION BY character_name ORDER BY date) AS is_access_prev,
                    CASE
                    WHEN is_access = TRUE AND LAG(is_access) OVER (PARTITION BY character_name ORDER BY date) = TRUE THEN TRUE
                    ELSE FALSE
                    END AS is_retained
                FROM
                    access_data
                ),

                consecutive_days_data AS (
                SELECT
                    *,
                    DATE_DIFF(date, LAG(date) OVER (PARTITION BY character_name ORDER BY date), DAY) = 1 AS is_consecutive,
                    SUM(CASE WHEN DATE_DIFF(date, LAG(date) OVER (PARTITION BY character_name ORDER BY date), DAY) = 1 THEN 0 ELSE 1 END)
                    OVER (PARTITION BY character_name ORDER BY date) AS group_id
                FROM
                    retention_data
                ),

                final_data AS (
                SELECT
                    *,
                    COUNT(*) OVER (PARTITION BY character_name, group_id) AS consecutive_days
                FROM
                    consecutive_days_data
                )

                SELECT
                date,
                character_name,
                character_level,
                FLOOR(character_level / 5) * 5 AS level_band,
                character_exp,
                character_exp_prev,
                exp_diff,
                is_access,
                is_access_prev,
                is_retained,
                consecutive_days
                FROM
                final_data
                ORDER BY
                character_name, date;


            """,
            "useLegacySql": False,  # Trueに設定すると、Legacy SQLを使用する
        }
    },
    gcp_conn_id='google_cloud_default',  # Airflowに設定した接続ID
)

# タスク依存性の定義
collect_rank_data >> bigquery_task
