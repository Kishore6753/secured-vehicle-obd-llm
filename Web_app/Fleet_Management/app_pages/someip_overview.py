import streamlit as st
import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

def show():
    st.title("🚗 Live SomeIP Dashboard")

    # Initialize Timestream client
    try:
        client = boto3.client('timestream-query', region_name='us-east-2')
    except (BotoCoreError, ClientError) as e:
        st.error(f"Failed to create Timestream client: {e}")
        st.stop()

    # Define queries
    queries = {
        "SOMEIP 1": """
            SELECT 
                time,
                MAX(CASE WHEN measure_name = 'Car_ID' THEN measure_value::varchar END) AS Car_ID,
                MAX(CASE WHEN measure_name = 'AttackSummary' THEN measure_value::varchar END) AS AttackSummary,
                MAX(CASE WHEN measure_name = 'Board' THEN measure_value::varchar END) AS Board
            FROM "FleetManagementDB"."SIPOneTable"
            GROUP BY time
            ORDER BY time DESC
        """,
        "SOMEIP 2": """
            SELECT 
                time,
                MAX(CASE WHEN measure_name = 'Car_ID' THEN measure_value::varchar END) AS Car_ID,
                MAX(CASE WHEN measure_name = 'AttackSummary' THEN measure_value::varchar END) AS AttackSummary,
                MAX(CASE WHEN measure_name = 'Board' THEN measure_value::varchar END) AS Board
            FROM "FleetManagementDB"."SIPTwoTable"
            GROUP BY time
            ORDER BY time DESC
        """
    }

    # Function to run a Timestream query and return DataFrame
    def run_query(query: str):
        try:
            response = client.query(QueryString=query)
            rows = response.get('Rows', [])
            columns = [col['Name'] for col in response.get('ColumnInfo', [])]

            if not rows or not columns:
                return pd.DataFrame()

            data = [[col.get('ScalarValue', '') for col in row['Data']] for row in rows]
            return pd.DataFrame(data, columns=columns)

        except (BotoCoreError, ClientError) as e:
            st.error(f"Query failed: {e}")
            return pd.DataFrame()

    # Query and show data for both SOMEIP tables
    for label, sql in queries.items():
        df = run_query(sql)
        st.subheader(f"🔍 Latest {label} Logs")
        if df.empty:
            st.warning(f"No data returned for {label}.")
        else:
            st.dataframe(df)

