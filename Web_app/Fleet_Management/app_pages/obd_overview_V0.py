import streamlit as st
import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

def show():
    st.title("🚗 Live OBD Error Dashboard")

    # Create Timestream client
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
        MAX(CASE WHEN measure_name = 'Location' THEN measure_value::varchar END) AS Location,
        MAX(CASE WHEN measure_name = 'Board' THEN measure_value::varchar END) AS Board,    
        MAX(CASE WHEN measure_name = 'Error_Code' THEN measure_value::varchar END) AS Error_Code
    FROM "FleetManagementDB"."OBDTable"
    GROUP BY time
    ORDER BY time DESC
    """

    # Execute Query
    try:
        response = client.query(QueryString=QUERY)
        rows = response['Rows']
        columns = [col['Name'] for col in response['ColumnInfo']]

        if not rows or not columns:
            st.warning("No data returned from Timestream.")
            st.stop()

        data = [[col.get('ScalarValue', '') for col in row['Data']] for row in rows]
        df = pd.DataFrame(data, columns=columns)

    except (BotoCoreError, ClientError) as e:
        st.error(f"Query failed: {e}")
        st.stop()

    # Display DataFrame
    st.subheader("🔍 Latest OBD Logs")
    st.dataframe(df)
