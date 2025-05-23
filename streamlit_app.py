#from turtle import onclick
import streamlit as st
import pandas as pd
import io
import requests
#import streamlit.components.v1 as components
st.set_page_config(layout="wide")

url="python_dash_catalog.xlsx"

# Use Streamlit's caching mechanism to read the Excel file
@st.cache_data
def load_data():
    df = pd.read_excel(url)
    return df

# Load the data
df = load_data()

# Display the DataFrame in the Streamlit app
df['Created_At'] = pd.to_datetime(df['Created_At'],  format='%d/%m/%Y %H:%M:%S',)
df['Modified_At'] = pd.to_datetime(df['Modified_At'],  format='%d/%m/%Y %H:%M:%S',)

df2 = df
# if 'df' not in st.session_state:
#    st.session_state.df = df

st.title('BigQuery Table Catalog')

def human_bytes(B):
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B, '')
    elif KB <= B < MB:
        return '{0:.2f}'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.2f}'.format(B / MB)
    elif GB <= B < TB:
        return '{0:.2f}'.format(B / GB)
    elif TB <= B:
        return '{0:.2f}'.format(B / TB)


def human_bytes_text(B):
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return 'Bytes'
    elif KB <= B < MB:
        return 'KB'
    elif MB <= B < GB:
        return 'MB'
    elif GB <= B < TB:
        return 'GB'
    elif TB <= B:
        return 'TB'


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return ('%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])).replace('.00', '')


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">',
                unsafe_allow_html=True)


def header_bg(table_type):
    if table_type == "BASE TABLE":
        return "tablebackground"
    elif table_type == "VIEW":
        return "viewbackground"
    else:
        return "mvbackground"


remote_css(
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.css")


local_css("style.css")
cb_view_details = st.sidebar.checkbox('View Details')

if cb_view_details:
    view_details=""
else:
    view_details="""style="display: none;" """

selectbox_orderby = st.sidebar.selectbox("Order By", ('A → Z', 'Z → A', 'Data Size ↓', 'Data Size ↑',
                                         'Rows ↓', 'Rows ↑', 'Date Created ↓', 'Date Created ↑', 'Date Altered ↓', 'Date Altered ↑'))
#button_clicked = st.button("OK")

all_option = pd.Series(['All'], index=[9999999])

#TABLE_SCHEMA=TABLE_SCHEMA.append({'resource_id':'All'},ignore_index = True)

if 'selectbox_database_key' not in st.session_state:
    st.session_state.selectbox_database_key = 10
    st.session_state.selectbox_schema_key = 20
    st.session_state.selectbox_owner_key = 30
    st.session_state.selectbox_table_type_key = 40
    st.session_state.selectbox_max_rows_key = 50
    st.session_state.selectbox_data_size_key = 60

# Table Catalog/Database
fv_database = df['dataset_id'].drop_duplicates()
fv_database = pd.concat([fv_database,all_option])

selectbox_database = st.sidebar.selectbox(
    'Dataset', fv_database, index=len(fv_database)-1, key=st.session_state.selectbox_database_key)

if selectbox_database != 'All':
    df = df.loc[df['dataset_id'] == selectbox_database]
else:
    df = df.loc[df['dataset_id'].isin(fv_database)]

# Table Schema
fv_table_schema = df['resource_id'].drop_duplicates()
fv_table_schema = pd.concat([fv_table_schema, all_option])

selectbox_schema = st.sidebar.selectbox(
    "Table", fv_table_schema, len(fv_table_schema)-1, key=st.session_state.selectbox_schema_key)

if selectbox_schema != 'All':
    df = df.loc[df['resource_id'] == selectbox_schema]
else:
    df = df.loc[df['resource_id'].isin(fv_table_schema)]

# Table Owner
fv_owner = df['OWNER'].drop_duplicates()
fv_owner = pd.concat([fv_owner,all_option])
selectbox_owner = st.sidebar.selectbox(
    "Table Owner", fv_owner, len(fv_owner)-1, key=st.session_state.selectbox_owner_key)

if selectbox_owner != 'All':
    df = df.loc[df['OWNER'] == selectbox_owner]
else:
    df = df.loc[df['OWNER'].isin(fv_owner)]

# Table Type
fv_table_type = df['Type'].drop_duplicates()
selectbox_table_type = st.sidebar.multiselect(
    'Type', fv_table_type, fv_table_type, key=st.session_state.selectbox_table_type_key)

if len(selectbox_table_type) > 0:
    df = df.loc[df['Type'].isin(selectbox_table_type)]
else:
    df = df.loc[df['Type'].isin(fv_table_type)]

# #!!! This part is disabled since sliders are causing performance issues with large datasets.!!!
# # data size selection
max_data_mb = int(df['Bytes'].max()/1048576)
step_size = 1

if max_data_mb>1000:
    step_size=10
elif max_data_mb>1000000:
    step_size=100
elif max_data_mb>1000000000:
    step_size=1000
elif max_data_mb>1000000000000:
    step_size=10000      

data_size = st.sidebar.slider(
    'Data Size (MB)', 0, max_data_mb+1, (0, max_data_mb+1), key=st.session_state.selectbox_data_size_key, step=step_size)
df = df.loc[(df['Bytes'] >= data_size[0]*1048576) &
            (df['Bytes'] <= data_size[1]*1048576)]

# rows selection
max_rows = int(df['N_Rows'].max())
step_size = 10

if max_rows>1000000:
    step_size=100
elif max_rows>1000000000:
    step_size=1000
elif max_rows>1000000000000:
    step_size=10000    

data_rows = st.sidebar.slider('Number of Rows', 0, max_rows+1,
                              (0, max_rows+1), key=st.session_state.selectbox_max_rows_key, step=step_size)
df = df.loc[(df['N_Rows'] >= data_rows[0]) &
            (df['N_Rows'] <= data_rows[1])]


def reset_button():
    st.session_state.selectbox_database_key = st.session_state.selectbox_database_key+1
    st.session_state.selectbox_schema_key = st.session_state.selectbox_schema_key+1
    st.session_state.selectbox_owner_key = st.session_state.selectbox_owner_key+1
    st.session_state.selectbox_table_type_key = st.session_state.selectbox_table_type_key+1
    st.session_state.selectbox_max_rows_key = st.session_state.selectbox_max_rows_key+1
    st.session_state.selectbox_data_size_key = st.session_state.selectbox_data_size_key+1


clear_button = st.sidebar.button(
    label='Clear Selections', on_click=reset_button)

if clear_button:
    df = df2

# Card order
orderby_column = ''
orderby_asc = True


if selectbox_orderby == 'A → Z':
    orderby_column = 'resource_id'
    orderby_asc = True
elif selectbox_orderby == 'Z → A':
    orderby_column = 'resource_id'
    orderby_asc = False
elif selectbox_orderby == 'Data Size ↓':
    orderby_column = 'Bytes'
    orderby_asc = False
elif selectbox_orderby == 'Data Size ↑':
    orderby_column = 'Bytes'
    orderby_asc = True
elif selectbox_orderby == 'Rows ↓':
    orderby_column = 'N_Rows'
    orderby_asc = False
elif selectbox_orderby == 'Rows ↑':
    orderby_column = 'N_Rows'
    orderby_asc = True
elif selectbox_orderby == 'Date Created ↓':
    orderby_column = 'Created_At'
    orderby_asc = False
elif selectbox_orderby == 'Date Created ↑':
    orderby_column = 'Created_At'
    orderby_asc = True
elif selectbox_orderby == 'Date Altered ↓':
    orderby_column = 'Modified_At'
    orderby_asc = False
elif selectbox_orderby == 'Date Altered ↑':
    orderby_column = 'Modified_At'
    orderby_asc = True


df.sort_values(by=[orderby_column], inplace=True, ascending=orderby_asc)



table_scorecard = """
<div class="ui five small statistics">
  <div class="grey statistic">
    <div class="value">"""+str(df[df['Type'] == 'TABLE']['resource_id'].count())+"""
    </div>
    <div class="grey label">
      Tables
    </div>
  </div>
    <div class="grey statistic">
        <div class="value">"""+str(df[df['Type'] == 'VIEW']['resource_id'].count())+"""
        </div>
        <div class="label">
        Views
        </div>
    </div>
    <div class="grey statistic">
        <div class="value">"""+str(df[df['Type'] == 'MATERIALIZED_VIEW']['resource_id'].count())+"""
        </div>
        <div class="label">
        Materialized Views
        </div>
    </div>    
  <div class="grey statistic">
    <div class="value">
      """+human_format(df['N_Rows'].sum())+"""
    </div>
    <div class="label">
      Rows
    </div>
  </div>

  <div class="grey statistic">
    <div class="value">
      """+human_bytes(df['Bytes'].sum())+" "+human_bytes_text(df['Bytes'].sum())+"""
    </div>
    <div class="label">
      Data Size
    </div>
  </div>
</div>"""

table_scorecard += """<br><br><br><div id="mydiv" class="ui centered cards">"""


for index, row in df.iterrows():
    table_scorecard += """
<div class="card"">   
    <div class=" content """+header_bg(row['Type'])+"""">
            <div class=" header smallheader">"""+row['dataset_id']+"""</div>
    <div class="meta smallheader">"""+row['resource_id']+"""</div>
    </div>
    <div class="content">
        <div class="description"><br>
            <div class="column kpi number">"""+human_format(row['N_Rows'])+"""<br>
                <p class="kpi text">Rows</p>
            </div>
            <div class="column kpi number">"""+human_bytes(row['Bytes'])+"""<br>
                <p class="kpi text">"""+human_bytes_text(row['Bytes'])+"""</p>
            </div>
            <div class="column kpi number">"""+"{0:}".format(row['N_Columns'])+"""<br>
                <p class="kpi text">Columns</b>
            </div>
        </div>
    </div>
    <div class="extra content">
        <div class="meta"><i class="table icon"></i> Table Type: """+(row['Type'])+"""</div>
        <div class="meta"><i class="user icon"></i> Owner: """+str(row['OWNER'])+""" </div>
        <div class="meta"><i class="calendar alternate outline icon"></i> Created On: """+(row['Created_At'].strftime("%Y-%m-%d"))+"""</div>
    </div>
    <div class="extra content" """+view_details+"""> 
        <div class="meta"><i class="edit icon"></i> Last Altered: """+(row['Modified_At'].strftime("%Y-%m-%d"))+"""</div>
        <div class="meta"><i class="comment alternate outline icon"></i> Comment: """+str(row['Description'])+""" </div>
        <div class="meta"><i class="external link icon"></i>Link: <a href="""+row['URL'] +""">BigQuery</a></div>
    </div>
</div>"""
    # <div class="extra content" """+view_details+"""> 
    #     <div class="meta"><i class="history icon"></i> Time Travel: """+str((row['RETENTION_TIME'])).strip(".0")+"""</div>
    #     <div class="meta"><i class="edit icon"></i> Last Altered: """+(row['LAST_ALTERED'].strftime("%Y-%m-%d"))+"""</div>
    #     <div class="meta"><i class="calendar times outline icon"></i> Transient: """+str(row['IS_TRANSIENT'])+""" </div>
    #     <div class="meta"><i class="th icon"></i> Auto Clustering: """+str(row['AUTO_CLUSTERING_ON'])+""" </div>
    #     <div class="meta"><i class="key icon"></i> Clustering Key: """+str(row['IS_TRANSIENT'])+""" </div>
    #     <div class="meta"><i class="comment alternate outline icon"></i> Comment: """+str(row['IS_TRANSIENT'])+""" </div>
    # </div>

st.markdown(table_scorecard, unsafe_allow_html=True)
