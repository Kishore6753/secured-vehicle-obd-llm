import streamlit as st
import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

def show():
    st.title("🚗 Live LSM Dashboard")

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
        MAX(CASE WHEN measure_name = 'Object' THEN measure_value::varchar END) AS Object,
        MAX(CASE WHEN measure_name = 'Board' THEN measure_value::varchar END) AS Board,
        MAX(CASE WHEN measure_name = 'Subject' THEN measure_value::varchar END) AS Subject,
        MAX(CASE WHEN measure_name = 'Access' THEN measure_value::varchar END) AS Access,
        MAX(CASE WHEN measure_name = 'Status' THEN measure_value::varchar END) AS Status
    FROM "FleetManagementDB"."LSMTable"
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
    st.subheader("🔍 Latest LSM Logs")
    st.dataframe(df)