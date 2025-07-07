import streamlit as st
import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

def show():
    st.title("🚗 Live Network Dashboard")

    # Initialize Timestream client
    try:
        client = boto3.client('timestream-query', region_name='us-east-2')
    except (BotoCoreError, ClientError) as e:
        st.error(f"Failed to create Timestream client: {e}")
        st.stop()

    # SQL Query
    QUERY = """
    SELECT 
        time,
        MAX(CASE WHEN measure_name = 'Car_ID' THEN measure_value::varchar END) AS Car_ID,
        MAX(CASE WHEN measure_name = 'AttackSummary' THEN measure_value::varchar END) AS AttackSummary,
        MAX(CASE WHEN measure_name = 'Board' THEN measure_value::varchar END) AS Board
    FROM "FleetManagementDB"."NetworkTable"
    GROUP BY time
    ORDER BY time DESC
    """

    # Execute query
    try:
        response = client.query(QueryString=QUERY)
        rows = response.get('Rows', [])
        columns = [col['Name'] for col in response.get('ColumnInfo', [])]

        if not rows or not columns:
            st.warning("No data returned from Timestream.")
            st.stop()

        # Parse rows
        data = [[col.get('ScalarValue', '') for col in row['Data']] for row in rows]
        df = pd.DataFrame(data, columns=columns)

    except (BotoCoreError, ClientError) as e:
        st.error(f"Query failed: {e}")
        st.stop()

    # Display table
    st.subheader("🔍 Latest Network Logs")
    st.dataframe(df)