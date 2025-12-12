
import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

DB_PATH = 'fleet_data.db'

def render():
    st.title('Settings - Admin')

    # simple admin check
    if st.session_state.get('role') != 'admin':
        st.error('Access denied. Admin only for Settings.')
        return

    st.header('Import / Export / DB Utilities')

    uploaded = st.file_uploader('Upload Excel or CSV to import (columns should match)', type=['xlsx','xls','csv'])
    if uploaded:
        try:
            if uploaded.name.lower().endswith('.csv'):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.write('Preview (first 10 rows)')
            st.dataframe(df.head(10))
            if st.button('Import to DB (replace table)'):
                for col in df.select_dtypes(include=['datetime','datetime64[ns]']).columns:
                    df[col] = df[col].astype(str)
                conn = sqlite3.connect(DB_PATH)
                df.to_sql('fleet', conn, if_exists='replace', index=False)
                conn.close()
                st.success('Imported to DB successfully.')
        except Exception as e:
            st.error(f'Import error: {e}')

    st.markdown('---')
    st.subheader('Export current DB')
    try:
        conn = sqlite3.connect(DB_PATH)
        existing = pd.read_sql_query('SELECT * FROM fleet', conn)
        conn.close()
        csv = existing.to_csv(index=False).encode('utf-8')
        st.download_button('⬇ Download CSV', csv, file_name='fleet_export.csv', mime='text/csv')
        towrite = BytesIO()
        with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
            existing.to_excel(writer, index=False, sheet_name='fleet')
            writer.save()
        towrite.seek(0)
        st.download_button('⬇ Download Excel', towrite.getvalue(), file_name='fleet_export.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        st.error(f'Export error: {e}')

    st.markdown('---')
    st.subheader('DB Utilities')
    if st.button('Create table if missing'):
        conn = sqlite3.connect(DB_PATH)
        conn.execute(\"\"\"CREATE TABLE IF NOT EXISTS fleet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Server TEXT,
            'Parent fleet' TEXT,
            'Fleet number' TEXT,
            Registration TEXT,
            'Repair status' TEXT,
            Comments TEXT,
            'Date created' TEXT,
            Priority INTEGER
        )\"\"\")
        conn.commit()
        conn.close()
        st.success('Table ensured.')
