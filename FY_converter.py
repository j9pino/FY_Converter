import streamlit as st
import pandas as pd
import requests
import json
import base64
import xlrd
from concurrent.futures import ThreadPoolExecutor

st.cache_data.clear()
st.set_page_config(page_title="FY Converter")
st.title("Pubs: Convert Calendar Year to Fiscal Year")

# Modify your Crossref API endpoint and headers accordingly
crossref_api_endpoint = 'https://api.crossref.org/works'
headers = {'Mailto': 'pinojc@ornl.gov'}

df = pd.DataFrame()  # Initial empty DataFrame

@st.cache_data(experimental_allow_widgets=True)
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="processedfile.csv">Download your processed CSV file</a>'

def fetch_data(DOI):
    try:
        r = requests.get(f'{crossref_api_endpoint}/{DOI}', headers=headers)
        rJSON = r.json()

        title = rJSON['message']['title'][0] if 'title' in rJSON['message'] else 'No Article Title Found'

        year = rJSON['message']['published']['date-parts'][0][0] if 'published' in rJSON['message'] else 'XXXX'
        month = rJSON['message']['published']['date-parts'][0][1] if 'published' in rJSON['message'] else 'XX'

        pub_date = f"{year}-{month}-XX"

        FY = 'NA' if month == 'XX' else (int(year) + 1 if int(month) >= fiscal_year_start_month else year)

    except:
        title, pub_date, FY = '', '', 'No published date found'

    return [DOI, title, pub_date, FY]

@st.cache_data(experimental_allow_widgets=True)
def api_loop(dataframe, fiscal_year_start_month):
    results_list = []
    total_len = len(dataframe)
    my_bar = st.progress(0.0)

    # Use ThreadPoolExecutor to parallelize API requests
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for idx, row in dataframe.iterrows():
            DOI = str(row['DOI']).replace(' ', '') if 'DOI' in row else ''
            future = executor.submit(fetch_data, DOI)
            futures.append(future)

        for idx, future in enumerate(futures):
            results = future.result()
            results_list.append(results)
            my_bar.progress((idx + 1) / total_len)

    dataframe['FY'] = [item[3] for item in results_list]
    st.dataframe(dataframe)

with st.form("my-form", clear_on_submit=True):
    data = st.file_uploader('Upload data. Make sure you have a column labeled "DOI". The standard RES output format is acceptable',
                            key='1',
                            help='This widget accepts both CSV and XLSX files. The standard RES output format is acceptable.')

    fiscal_year_start_month = st.select_slider(
        "Select Fiscal Year Start Month",
        options=list(range(1, 13)),
        value=1
    )

    submitted = st.form_submit_button("Start the Process")

    if submitted and data is not None:
        st.write("Your Data:")
        if data.name.lower().endswith('.csv'):
            df = pd.read_csv(data, header=[0])
            st.dataframe(df)
            api_loop(df, fiscal_year_start_month)
            st.balloons()
            st.success('The "FY" column has been appended to the original file!')

        elif data.name.lower().endswith('.xlsx') or data.name.lower().endswith('.xls'):
            df = pd.read_excel(data, header=[0])
            st.dataframe(df)
            api_loop(df, fiscal_year_start_month)
            st.balloons()
            st.success('The "FY" column has been appended to the original file!')

if 'FY' in df.columns:
    st.markdown(get_table_download_link(df), unsafe_allow_html=True)
