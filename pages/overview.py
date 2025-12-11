
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

def render():
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
        st.warning("No data — upload an Excel file in Settings.")
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

    df['_status'] = df[status_col].astype(str).fillna('Other').str.strip()

    # compute counts and order
    counts = df['_status'].value_counts()
    preferred = ['New','New - vetted','Inspected - monitoring','Awaiting material','Offline- pending vetting']
    # build display list
    display = []
    for p in preferred:
        if p in counts.index:
            display.append(p)
    for s in counts.index:
        if s not in display and len(display) < 5:
            display.append(s)
    while len(display) < 5:
        display.append('Other')

    color_map = {'New':'#FF6B6B','New - vetted':'#FFA751','Inspected - monitoring':'#FFD93D',
                 'Awaiting material':'#4DA3FF','Offline- pending vetting':'#43E97B','Other':'#888888'}

    cols = st.columns(5, gap='large')
    for c,s in zip(cols, display):
        val = int(counts.get(s,0))
        color = color_map.get(s,'#666666')
        c.markdown(f"""<div style='background:linear-gradient(135deg,{color},#222); padding:18px; border-radius:10px; color:white; text-align:center; box-shadow:0 6px 18px rgba(0,0,0,0.18);'>
                <div style='font-size:15px; font-weight:700'>{s}</div>
                <div style='font-size:34px; font-weight:800; margin-top:6px'>{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('---')

    # pie chart
    chart_df = counts.reset_index()
    chart_df.columns = ['Status','Count']
    fig = px.pie(chart_df, values='Count', names='Status', title='Repair Status Distribution', color='Status')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('---')

    # priority bars
    prio_col = None
    for cand in ['Priority','priority']:
        if cand in df.columns:
            prio_col = cand
            break
    if prio_col:
        prio_counts = df[prio_col].fillna(0).astype(int).value_counts().sort_index()
        st.subheader('Priority Distribution')
        pcols = st.columns(3)
        labels = [1,2,3]
        colors_p = {1:'#FF4D4F',2:'#FFD24D',3:'#34D399'}
        for pc,lab in zip(pcols,labels):
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
