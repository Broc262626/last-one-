
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

def render():
    st.set_page_config(layout='wide')
    st.title("Fleet Health — Overview")

    conn = sqlite3.connect("fleet_data.db")
    try:
        df = pd.read_sql_query("SELECT * FROM fleet", conn)
    except Exception as e:
        st.error(f"DB read error: {e}")
        conn.close()
        return
    conn.close()

    if df.empty:
        st.info("No data found. Go to Settings and import your Excel file.")
        return

    # detect repair status column
    status_col = None
    for cand in ['Repair status','repairStatus','Repair Status','Status']:
        if cand in df.columns:
            status_col = cand
            break
    if status_col is None:
        st.error("'Repair status' column not found in data.")
        return

    # normalize and compute counts
    df['_status'] = df[status_col].astype(str).fillna('Other').str.strip()
    counts = df['_status'].value_counts()

    # Display modern status bars (horizontal)
    st.subheader('Repair Status — Overview')
    total = counts.sum()
    for status, color in [
        ('New','#FF6B6B'),('New - vetted','#FFA751'),('inspected - monitoring','#FFD93D'),
        ('Awaiting material','#4DA3FF'),('Offline- pending vetting','#43E97B')]:
        cnt = int(counts.get(status,0))
        pct = (cnt/total*100) if total>0 else 0
        st.markdown(f"""<div style='background:#0b1220; padding:6px; border-radius:8px; margin-bottom:8px'>
            <div style='display:flex; justify-content:space-between; color:#e6eef8; font-weight:600'>
                <div>{status}</div>
                <div>{cnt} ({pct:.0f}%)</div>
            </div>
            <div style='background:#071225; height:10px; border-radius:6px; margin-top:6px'>
                <div style='width:{pct:.0f}%; background:linear-gradient(90deg,{color},#222); height:10px; border-radius:6px'></div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('---')

    # pie chart
    chart_df = counts.reset_index()
    chart_df.columns = ['Status','Count']
    fig = px.pie(chart_df, values='Count', names='Status', title='Repair Status Distribution')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('---')

    # Priority bars
    prio_col = None
    for cand in ['Priority','priority']:
        if cand in df.columns:
            prio_col = cand
            break
    if prio_col:
        st.subheader('Priority Distribution')
        prio_counts = df[prio_col].fillna(0).astype(int).value_counts().sort_index()
        pcols = st.columns(3)
        colors_p = {1:'#FF4D4F',2:'#FFD24D',3:'#34D399'}
        for pc,lab in zip(pcols,[1,2,3]):
            pc.markdown(f"""<div style='background:{colors_p[lab]}; padding:12px; border-radius:8px; color:black; text-align:center; font-weight:700'>
                            <div style='font-size:14px'>Priority {lab}</div>
                            <div style='font-size:28px'>{int(prio_counts.get(lab,0))}</div>
                          </div>""", unsafe_allow_html=True)
    else:
        st.info('No Priority column found in data.')

    st.markdown('---')
    st.subheader('Quick view (first 20 rows)')
    show_cols = ['Parent fleet','Fleet number', status_col, 'Comments','Priority']
    present = [c for c in show_cols if c in df.columns]
    st.dataframe(df[present].head(20), use_container_width=True)
