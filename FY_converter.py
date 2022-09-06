import streamlit as st
import pandas as pd
import requests, json
import time

st.experimental_memo.clear()
st.set_page_config(page_title="FY Converter")
st.title("Pubs: Calendar Year to Fiscal Year")
bacon = ''
#Scopus API headers
headers = {'X-ELS-APIKey': st.secrets['API_KEY'], 
           'Accept': 'application/json'}

#Scopus API query 
url = 'https://api.elsevier.com/content/abstract/doi/'

#create empty lists to which we will append API-gathered data
results_list = []
csv_thing = None
   
#convert dataframe to csv for exporting purposes
@st.experimental_memo(suppress_st_warning=True)
def convert_df_to_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

#main function that uses list of DOIs with API call
@st.experimental_memo(suppress_st_warning=True)
def api_loop(dataframe):
    global csv_thing
    global dates_df
    for i in range(len(df)):
        percent_complete = (i+1)/len(df)
        DOI = str(df.iloc[i]['DOIs'])
        queryURL = url + DOI
        r = requests.get(queryURL, headers=headers)
        rText = r.text
        rJSON = json.loads(rText)
        try:
            coverDate = rJSON['abstracts-retrieval-response']['coredata']['prism:coverDate']
        except:
            coverDate = 'No Date Found'
        try:
            times_cited = rJSON['abstracts-retrieval-response']['coredata']['citedby-count']
        except:
            times_cited = 'No Citations Found'
        try:
            if int(coverDate[5:7]) >= 10:
                year = int(coverDate[:4])+1
            else:
                year = int(coverDate[:4])
        except ValueError:
            year = 'No Date Found'
        results_list.append([DOI,coverDate,times_cited,year])
        my_bar.progress(percent_complete)
        time.sleep(0.05)
    dates_df = pd.DataFrame(results_list, columns = ['DOI','coverDate','Times Cited', 'FY'])
    
    dates_df = dates_df.reset_index(drop=True)
    dates_df['FY'] = dates_df['FY'].astype(str)
    dates_df['coverDate'] = dates_df['coverDate'].astype(str)
    
    #display final dataframe
    dates_df = dates_df.drop_duplicates()
    st.dataframe(dates_df)
       
    #convert df to csv
    csv_thing = convert_df_to_csv(dates_df)

@st.experimental_memo(suppress_st_warning=True)
def show_download_button():
    global csv_thing
    st.download_button(
        label="Download data as CSV",
        data=csv_thing,
        file_name='DOIs_with_FY.csv',
        mime='text/csv')
         
#streamlit upload button
data = st.file_uploader("Upload a CSV of DOIs, one per line, no header column",
                       key = '1',
                       help='Make sure your upload file is a CSV and only contains DOIs, one per line, with no header')

#read in uploaded CSV and write to dataframe
if data is not None:
    df = pd.read_csv(data, header=None)
    df = df.rename(columns={0: 'DOIs'})
    #display dataframe of uploaded DOIs     
    st.dataframe(df)
    #introduce streamlit proress bar widget
    my_bar = st.progress(0.0)
    api_loop(df)
    if csv_thing is not None:
        st.balloons()              
        st.success('Your Download is Ready!')
        show_download_button()
