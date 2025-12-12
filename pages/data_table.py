
import streamlit as st
import sqlite3
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from io import BytesIO

def render():
    st.title("Data Table — Excel-style")

    DB_PATH = "fleet_data.db"
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM fleet", conn)
    except Exception as e:
        st.error(f"DB read error: {e}")
        conn.close()
        return
    conn.close()

    if df.empty:
        st.info("No data. Upload via Settings page.")
        return

    if 'id' not in df.columns:
        df = df.reset_index().rename(columns={'index':'id'})

    # detect status and priority col names
    status_col = None
    for cand in ['Repair status','repairStatus','Repair Status','Status']:
        if cand in df.columns:
            status_col = cand
            break
    priority_col = None
    for cand in ['Priority','priority']:
        if cand in df.columns:
            priority_col = cand
            break

    status_options = sorted([str(x) for x in df[status_col].dropna().unique()]) if status_col else []

    priority_js = JsCode(\"\"\"function(params) {
        if (params.value == 1 || params.value === '1') return {'backgroundColor':'#ff4d4f','color':'white','fontWeight':'700','textAlign':'center'};
        if (params.value == 2 || params.value === '2') return {'backgroundColor':'#ffd24d','color':'black','fontWeight':'700','textAlign':'center'};
        if (params.value == 3 || params.value === '3') return {'backgroundColor':'#34d399','color':'black','fontWeight':'700','textAlign':'center'};
        return null;
    }\"\"\")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, filter=True, sortable=True, resizable=True)
    if status_col:
        gb.configure_column(status_col, cellEditor='agSelectCellEditor', cellEditorParams={'values':status_options})
    if priority_col:
        gb.configure_column(priority_col, cellEditor='agSelectCellEditor', cellEditorParams={'values':[1,2,3]}, cellStyle=priority_js, width=100)
    gb.configure_column('id', editable=False, header_name='ID', width=80)
    gb.configure_selection('single')

    grid_options = gb.build()
    grid_response = AgGrid(df, gridOptions=grid_options, update_mode=GridUpdateMode.VALUE_CHANGED,
                          allow_unsafe_jscode=True, fit_columns_on_grid_load=True, enable_enterprise_modules=False, theme='streamlit')

    updated = pd.DataFrame(grid_response['data'])

    st.markdown('---')
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button('💾 Save changes to DB'):
            try:
                if priority_col and priority_col in updated.columns:
                    updated[priority_col] = pd.to_numeric(updated[priority_col], errors='coerce').fillna(0).astype(int)
                conn = sqlite3.connect(DB_PATH)
                updated.to_sql('fleet', conn, if_exists='replace', index=False)
                conn.close()
                st.success('Saved to DB. Reload page to view changes.')
            except Exception as e:
                st.error(f'Save error: {e}')
    with c2:
        selected = grid_response.get('selected_rows', [])
        if st.button('🗑 Delete selected row'):
            if not selected:
                st.warning('Select a row first.')
            else:
                sel = selected[0]
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    if 'id' in sel:
                        cur.execute('DELETE FROM fleet WHERE id=?', (int(sel['id']),))
                        conn.commit()
                    else:
                        tmp = pd.DataFrame(grid_response['data'])
                        tmp.to_sql('fleet', conn, if_exists='replace', index=False)
                    conn.close()
                    st.success('Deleted. Reloading...')
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f'Delete error: {e}')
    with c3:
        csv = updated.to_csv(index=False).encode('utf-8')
        st.download_button('⬇ Download CSV (current view)', csv, file_name='fleet_export.csv', mime='text/csv')
