import streamlit as st
import pandas as pd
import requests
import json
import time
import base64

st.cache_data.clear()
st.set_page_config(page_title="FY Converter")
st.title("Pubs: Convert Calendar Year to Fiscal Year")

headers = {'Mailto': 'pinojc@ornl.gov'}

# create empty lists to which we will append API-gathered data
results_list = []

# Define the get_table_download_link function
@st.cache_data(experimental_allow_widgets=True)
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:file/csv;base64,{b64}" download="processedfile.csv">Download your processed CSV file</a>'

# Define an empty DataFrame
df = pd.DataFrame(columns=['DOI', 'title', 'pub_date', 'FY'])

# Boolean variable to track whether the program has run
program_has_run = False

# main function that uses list of DOIs with API call
@st.cache_data(experimental_allow_widgets=True)
def api_loop(dataframe, fiscal_year_start_month):
    global df, program_has_run  # Make df and program_has_run global so that we can update them
    program_has_run = True
    for i in range(len(df)):
        percent_complete = (i + 1) / len(df)
        try:
            DOI = str(df.iloc[i]['DOI'].replace(' ', ''))
        except:
            DOI = ''
            title = ''
            pub_date = ''
            FY = ''
            results_list.append([DOI, title, pub_date, FY])
            my_bar.progress(percent_complete)
            continue
        r = requests.get('https://api.crossref.org/works/' + DOI + '?mailto=pinojc@ornl.gov')
        rText = r.text
        try:
            rJSON = json.loads(rText)
        except:
            DOI = ''
            title = ''
            pub_date = ''
            FY = ''
            results_list.append([DOI, title, pub_date, FY])
            my_bar.progress(percent_complete)
            continue
        try:
            title = rJSON['message']['title'][0]
        except:
            title = 'No Article Title Found'
        try:
            try:
                year = rJSON['message']['published']['date-parts'][0][0]
            except:
                year = 'XXXX'
            try:
                month = rJSON['message']['published']['date-parts'][0][1]
            except:
                month = 'XX'
            try:
                day = rJSON['message']['published']['date-parts'][0][2]
            except:
                day = 'XX'
            pub_date = str(year) + '-' + \
                       str(month) + '-' + \
                       str(day)
        except:
            pub_date = ''
        try:
            if month == 'XX':
                FY = 'NA'
            elif int(month) >= fiscal_year_start_month:
                FY = int(year) + 1
            else:
                FY = year
        except:
            FY = 'No published date found'
        results_list.append([DOI, title, pub_date, FY])
        my_bar.progress(percent_complete)
        time.sleep(0.05)
    
    # Append the 'FY' column to the original DataFrame
    df['FY'] = [item[3] for item in results_list]

    # Display the updated original DataFrame
    st.dataframe(df)

with st.form("my-form", clear_on_submit=True):
    data = st.file_uploader('Upload data.  Make sure you have a column labeled "DOI". The standard RES output format is acceptable',
                           key='1',
                           help='This widget accepts both CSV and XLSX files. The standard RES output format is acceptable.')

    fiscal_year_start_month = st.select_slider(
        "Select Fiscal Year Start Month",
        options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        value=1
    )

    submitted = st.form_submit_button("Start the Process")

    if submitted and data is not None:
        st.write("Your Data:")
        if data.name.lower().endswith('.csv'):
            df = pd.read_csv(data, header=[0])
            # display dataframe of uploaded DOIs
            st.dataframe(df)
            # introduce streamlit progress bar widget
            my_bar = st.progress(0.0)
            api_loop(df, fiscal_year_start_month)
            st.balloons()
            st.success('The "FY" column has been appended to the original file!')

        elif data.name.lower().endswith('.xlsx'):
            df = pd.read_excel(data, header=[0])
            # display dataframe of uploaded DOIs
            st.dataframe(df)
            # introduce streamlit progress bar widget
            my_bar = st.progress(0.0)
            api_loop(df, fiscal_year_start_month)
            st.balloons()
            st.success('The "FY" column has been appended to the original file!')

# Add a download button for the updated DataFrame only if the program has run
if program_has_run and 'FY' in df.columns:
    st.markdown(get_table_download_link(df), unsafe_allow_html=True)
