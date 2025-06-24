import requests
import pandas as pd
import time
from google.cloud import bigquery
import os
from dotenv import load_dotenv
from datetime import datetime
from tqdm import tqdm
from google.api_core.exceptions import NotFound



# 환경 변수 설정
load_dotenv('/Users/hongseoklee/VSCodeWorkspace/MapleAnalysis/keys/keys.env')

# 환경 변수 설정 (Google Cloud 인증 정보)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/hongseoklee/VSCodeWorkspace/MapleAnalysis/keys/gameanalysis-440113-4b375da6b7e2.json"

# 설정 변수
API_KEY = os.getenv("API_KEY")
START_DATE = "2024-06-15"  # 수집 시작 날짜
END_DATE = "2024-06-30"    # 수집 종료 날짜

BIGQUERY_PROJECT_ID = "gameanalysis-440113"
BIGQUERY_DATASET_ID = "maplestory_data"
BIGQUERY_TABLE_ID = "AuroraRankTable"

# 테이블 스키마 정의
TABLE_SCHEMA = [
    bigquery.SchemaField("date", "DATETIME", mode="NULLABLE"),
    bigquery.SchemaField("page", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("ranking", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("character_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("world_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("class_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("sub_class_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("character_level", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("character_exp", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("character_popularity", "INTEGER", mode="NULLABLE"),
]

def get_existing_date_page_set(client, dataset_id, table_id):
    """BigQuery에서 이미 존재하는 date와 page 조합을 가져오는 함수"""
    query = f"""
    SELECT DISTINCT date, page
    FROM `{client.project}.{dataset_id}.{table_id}`
    """
    query_job = client.query(query)
    results = query_job.result()
    existing_set = set()
    for row in results:
        existing_set.add((row.date.strftime("%Y-%m-%d"), row.page))
    return existing_set

def collect_data(api_key, date, existing_date_page_set):
    """특정 날짜에 대해 캐릭터 랭크 데이터를 수집하는 함수"""
    headers = {
        "x-nxopen-api-key": api_key
    }

    data = []
    max_page = 70000

    for page in tqdm(range(1, max_page + 1)):
        # 이미 수집된 date와 page 조합이면 건너뛰기
        if (date, page) in existing_date_page_set:
            #print(page, "의 정보가 이미 존재합니다.")
            continue

        url = "https://open.api.nexon.com/maplestory/v1/ranking/overall"
        params = {
            "date": date,
            "page": page,
            "world_name": "오로라",
            "world_type": 0
        }
        response = requests.get(url, headers=headers, params=params)

        # 응답 코드 확인
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        json_data = response.json()
        rankings = json_data.get("ranking", [])

        # 데이터가 없으면 루프 종료
        if not rankings:
            print(f"{date}의 페이지 {page}에서 데이터를 찾을 수 없습니다.")
            break

        # 필요한 데이터 추출 및 페이지 번호 추가
        for rank in rankings:
            data.append({
                "date": date,
                "page": page,
                "ranking": rank.get("ranking"),
                "character_name": rank.get("character_name"),
                "world_name": rank.get("world_name"),
                "class_name": rank.get("class_name"),
                "sub_class_name": rank.get("sub_class_name"),
                "character_level": rank.get("character_level"),
                "character_exp": rank.get("character_exp"),
                "character_popularity": rank.get("character_popularity"),
            })

        time.sleep(1)  # API 호출 제한 고려하여 딜레이 추가

    return data

def upload_to_bigquery(df, project_id, dataset_id, table_id):
    """데이터프레임을 BigQuery에 업로드하는 함수"""
    client = bigquery.Client(project=project_id)
    table_ref = client.dataset(dataset_id).table(table_id)

    # 테이블이 존재하는지 확인하고, 없으면 생성
    try:
        client.get_table(table_ref)
        print(f"{table_id} 테이블이 이미 존재합니다.")
    except Exception:
        print(f"{table_id} 테이블이 존재하지 않습니다. 새로 생성합니다.")
        table = bigquery.Table(table_ref, schema=TABLE_SCHEMA)
        client.create_table(table)
        print(f"{table_id} 테이블이 생성되었습니다.")

    # 데이터 타입 변환 및 컬럼 순서 정렬
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    numeric_fields = ["page", "ranking", "character_level", "character_exp", "character_popularity"]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df[field], errors='coerce').astype('Int64')

    string_fields = ["character_name", "world_name", "class_name", "sub_class_name"]
    for field in string_fields:
        df[field] = df[field].astype(str)

    # 테이블 스키마에 따라 컬럼 순서 맞춤
    df = df[[field.name for field in TABLE_SCHEMA]]

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=TABLE_SCHEMA
    )

    try:
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        print(f"{job.output_rows}개의 행이 {dataset_id}.{table_id} 테이블에 업로드되었습니다.")
    except Exception as e:
        print(f"BigQuery 업로드 중 오류 발생: {e}")

def main():
    # BigQuery 클라이언트 생성
    client = bigquery.Client(project=BIGQUERY_PROJECT_ID)

    # 테이블이 존재하는지 확인하고, 없으면 미리 생성
    table_ref = client.dataset(BIGQUERY_DATASET_ID).table(BIGQUERY_TABLE_ID)
    try:
        table_obj = client.get_table(table_ref)
        print(f"테이블 {BIGQUERY_TABLE_ID}이(가) 이미 존재합니다.")
    except NotFound:
        print(f"테이블 {BIGQUERY_TABLE_ID}을(를) 찾을 수 없습니다. 새로 생성합니다.")
        table = bigquery.Table(table_ref, schema=TABLE_SCHEMA)
        client.create_table(table)
        print(f"테이블 {BIGQUERY_TABLE_ID} 생성 완료.")


    # 기존의 date와 page 조합 가져오기
    existing_date_page_set = get_existing_date_page_set(client, BIGQUERY_DATASET_ID, BIGQUERY_TABLE_ID)

    # 날짜 범위 생성
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='D').strftime("%Y-%m-%d").tolist()

    # 날짜 범위 내의 각 날짜에 대해 데이터 수집 및 업로드
    for date in date_range:
        print(f"{date}의 데이터를 수집합니다.")
        daily_data = collect_data(API_KEY, date, existing_date_page_set)
        if daily_data:
            df_daily = pd.DataFrame(daily_data)

            # BigQuery 업로드
            upload_to_bigquery(df_daily, BIGQUERY_PROJECT_ID, BIGQUERY_DATASET_ID, BIGQUERY_TABLE_ID)
            print(f"{date} 데이터 수집 및 업로드 완료")
        else:
            print(f"{date}에 대한 데이터가 없습니다.")

if __name__ == "__main__":
    main()
    