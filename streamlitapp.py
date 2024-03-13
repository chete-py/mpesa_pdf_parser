import streamlit as st
import pandas as pd
import numpy as np
import fitz
import re
import plotly.graph_objects as go 
import re
from local_components import card_container
import streamlit_shadcn_ui as ui
import base64

st.set_page_config(page_icon="mpesa.jpg", page_title = 'Mpesa Statement Parser ', layout="wide")

st.sidebar.image('mpesa.jpg', use_column_width=True)

uploaded_file = st.sidebar.file_uploader("Upload M-Pesa Statement",  type='pdf')


text_list = []  # List to store text from each page

if uploaded_file is not None:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    for page in doc:
        text_list.append(page.get_text())

    doc.close()

    # Join the text from all pages into a single string
    text = "\n".join(text_list)


    newdata = text.replace("   ", "")
    data = newdata.replace("\n", "|")

    pd.set_option('display.max_rows', None)

    # Define a regex pattern to match dates and corresponding information up to the first full stop
    pattern = re.compile(r'(\d{4}-\d{2}-\d{2})\s(.*?\.\d)', re.DOTALL)

    # Find all matches in the massive string
    matches = pattern.findall(data)

    df = pd.DataFrame(matches, columns=['Date', 'Information'])

    df['Time'] = df['Information'].str.split('|').str[0]
    df['Amount'] = df['Information'].str.split('|').str[-1]
    df['Persons'] = df['Information'].str.split('|').str[2]
    df['Involved'] = df['Information'].str.split('|').str[3]
    df['Involved'] = df['Involved'].str.replace('Completed', '')
    df['Account Involved'] = df['Persons'] + " " + df['Involved']
    df['Usage'] = df['Information'].str.split('|').str[1]

    # Define a regex pattern to match non-digit values
    non_digit_pattern = r'\D+'

    # Extract digit values and replace the 'Usage' column
    df['Usage'] = df['Usage'].str.extract(f'({non_digit_pattern})')

    # Define a regex pattern to match everything after the string 'payment'
    payment_pattern = r'\bPayment\b.*'

    # Replace the 'Description' column with the modified values
    df['Usage'] = df['Usage'].str.replace(payment_pattern, 'Payment Online', regex=True)

    # Define a regex pattern to match 'to' with a space before it
    filler_pattern = r'\s(?:to|from|by)\b.*'

    # Replace the 'Description' column with the modified values
    df['Usage'] = df['Usage'].str.replace(filler_pattern, '', regex=True)


    # Identify rows where 'Description' starts with 'customer' and replace the values
    mask = df['Usage'].str.startswith('Customer Transfer of Funds')
    df.loc[mask, 'Usage'] = 'Transfer Of Funds Charge'

    df['Usage'] = df['Usage'].str.strip()

    df['Account Involved'] = df['Account Involved'].str.replace('Business to -', '')

    # Define a regex pattern to match everything after the string 'completed'
    pattern = r'\bCompleted\b.*'

    # Replace the 'Description' column with the modified values
    df['Account Involved'] = df['Account Involved'].str.replace(pattern, 'Nan', regex=True)

    df['Account Involved'] = df['Account Involved'].str.strip()

    # Replace 'NA' values in 'Column1' with values from 'Column2'
    df['Account Involved'] = df['Account Involved'].replace('Nan', np.nan).combine_first(df['Usage'])

    # Define a regex pattern to match everything after the string 'completed'
    newpattern = r'\bOriginal conversation\b.*'

    # Replace the 'Description' column with the modified values
    df['Account Involved'] = df['Account Involved'].str.replace(newpattern, '', regex=True)


    

    df['Amount'] = df['Amount'].str.replace(',', '')

    df['Amount'] = pd.to_numeric(df['Amount'])
    df['Amount'] = round(df['Amount'], 0)


    df['Date'] = pd.to_datetime(df['Date'] , errors='coerce')

    # Extract the day of the week, month and create new columns
    df['Day'] = df['Date'].dt.day_name()
    df['Month'] = df['Date'].dt.strftime('%B')

    # Remove the time component
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    newdf = df[['Date', 'Month', 'Day', 'Time', 'Usage', 'Account Involved', 'Amount']]

    newdf['Usage'] = newdf['Usage'].replace('Completed', 'Buy Bundles')
    newdf['Account Involved'] = newdf['Account Involved'].replace('Completed', 'Safaricom Bundles')   


    finaldf = newdf[['Date', 'Time', 'Usage', 'Account Involved', 'Amount']]

    payments = newdf[newdf['Amount'] < 0]
    receipts = newdf[newdf['Amount'] > 0]

    payments['Amount'] = payments['Amount'] / -1 

    months = receipts.groupby('Month')['Amount'].sum().reset_index()
    day = receipts.groupby('Day')['Amount'].sum().reset_index()

    highest_receipt = receipts[receipts['Amount'] == receipts['Amount'].max()]
    highest = "{:,.0f}".format(highest_receipt['Amount'].iloc[0])
    highest_description = highest_receipt['Account Involved'].iloc[0]
    final_description = highest_description.split('-')[-1]

    

    highest_amount_for_month = months['Amount'].max()
    highest_month_row = months[months['Amount'] == highest_amount_for_month]
    highest_month = highest_month_row['Month'].iloc[0]
    highest_month_amount = "{:,.0f}".format(highest_month_row['Amount'].iloc[0])
   

    highest_amount_for_day = day['Amount'].max()
    highest_day_row = day[day['Amount'] == highest_amount_for_day]
    highest_day = highest_day_row['Day'].iloc[0]
    highest_day_amount = "{:,.0f}".format(highest_day_row['Amount'].iloc[0])


    grouped = receipts.groupby('Usage')['Amount'].sum().reset_index()
    receipt_account = (receipts.groupby('Account Involved')['Amount'].sum().reset_index())
    frequent_receipt_account = receipt_account.sort_values(by='Amount', ascending=False).reset_index(drop=True)
    top_receipts = frequent_receipt_account.head(10)


    months_payments = payments.groupby('Month')['Amount'].sum().reset_index()
    day_payments = payments.groupby('Day')['Amount'].sum().reset_index()

    highest_payment = payments[payments['Amount'] == payments['Amount'].max()]
    format_highest = "{:,.0f}".format(highest_payment['Amount'].iloc[0])
    highest_description_payments = highest_payment['Account Involved'].iloc[0]

   

    highest_amount_for_month_payments = months_payments['Amount'].max()
    highest_month_row_payments = months_payments[months_payments['Amount'] == highest_amount_for_month_payments]
    highest_month_payments = highest_month_row_payments['Month'].iloc[0]
    highest_month_amount_payments = "{:,.0f}".format(highest_month_row_payments['Amount'].iloc[0])
   

    highest_amount_for_day_payments = day_payments['Amount'].max()
    highest_day_row_payments = day_payments[day_payments['Amount'] == highest_amount_for_day_payments]
    highest_day_payments = highest_day_row_payments['Day'].iloc[0]
    highest_day_amount_payments = "{:,.0f}".format(highest_day_row_payments['Amount'].iloc[0])


    
    payment_account = (payments.groupby('Account Involved')['Amount'].sum().reset_index())
    frequent_payment_account = payment_account.sort_values(by='Amount', ascending=False).reset_index(drop=True)
    top_payments =  frequent_payment_account.head(10)


    graph1 = receipts.groupby('Usage')['Amount'].sum().sort_values(ascending=False).head(10).reset_index()
    graph2 = payments.groupby('Usage')['Amount'].sum().sort_values(ascending=False).head(10).reset_index()

    # GET CUSTOMER DETAILS

    newpattern = re.compile(r"Customer(.*?)TRANSACTION TYPE", re.DOTALL)

    # Find all matches in the massive string
    newmatches = newpattern.findall(data)

    #Convert list to string
    new = ' '.join(map(str, newmatches))

    customer  = new.replace('|', " _")

    name = customer.split('_')[1]
    phone = customer.split('_')[3]
    period = customer.split('_')[7]

    st.markdown(f"Name: {name} <br> Phone: {phone}  <br>Period: {period}", unsafe_allow_html=True)

    with card_container(key='global'):
        tab1, tab2, tab3= st.tabs(["📈 Money In", "📈Money Out", "🗃 Records"])
        with tab1:
            with card_container(key='dashboard'):
                cols = st.columns(3)
                with cols[0]:
                    ui.metric_card(title="Highest Receipt", content=f'Ksh. {highest}', description= f"{final_description}", key="card1")
                with cols[1]:
                    ui.metric_card(title="Frequent Month", content=f'{highest_month}', description= f"Ksh. {highest_month_amount}", key="card2")
                with cols[2]:
                    ui.metric_card(title="Frequent Day", content = f'{highest_day}', description= f"Ksh. {highest_day_amount}", key="card3")


            with card_container(key='graph'):
                tab4, tab5  = st.tabs(["Receipts Analysis", "Frequent Accounts"])
                with tab4:
                    # Calculate the sum of amounts for each category              
                    fig = go.Figure()

                    fig.add_trace(go.Bar(
                            width= 0.35,
                            x = graph1['Usage'],
                            y= graph1['Amount'],   
                            name = 'Actual',
                            marker_color="#00A550"
                            
                            ))               
                    
                            
                    
                    fig.update_layout(title={'text': 'RECEIPT ANALYSIS', 'x': 0.5, 'xanchor': 'center'},  width=875,
                                            xaxis_title='Category',
                                            yaxis_title='Amount',
                                            xaxis=dict(tickfont=dict(size=9.2)),                                  
                                            )
                    
                    fig.update_xaxes(tickangle=90)

                    st.plotly_chart(fig)
                
                with tab5:
                    st.table(top_receipts)

                    if st.button("Download Receipt CSV"):
                        csv_data = frequent_receipt_account.to_csv(index=False, encoding='utf-8')
                        b64 = base64.b64encode(csv_data.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="top_receipts_mpesastatement.csv">Download CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)   

        
    
        with tab2:
            with card_container(key='form'):   
                cols = st.columns(3)
                with cols[0]:
                    ui.metric_card(title="Highest Payment", content=f'Ksh. {format_highest}', description= f"{highest_description_payments}", key="card4")
                with cols[1]:
                    ui.metric_card(title="Frequent Month", content=f'{highest_month_payments}', description= f"Ksh. {highest_month_amount_payments}", key="card5")
                with cols[2]:
                    ui.metric_card(title="Frequent Day", content = f'{highest_day_payments}', description= f"Ksh. {highest_day_amount_payments}", key="card6")


            with card_container(key='graph'):
                tab6, tab7  = st.tabs(["Payment Analysis", "Frequent Accounts"])
                with tab6:
                    # Calculate the sum of amounts for each category              
                    fig2 = go.Figure()

                    fig2.add_trace(go.Bar(
                            width= 0.35,
                            x = graph2['Usage'],
                            y= graph2['Amount'],   
                            name = 'Actual',
                            marker_color="#4169e1"

                            
                            ))               
                    
                            
                    
                    fig2.update_layout(title={'text': 'PAYMENT ANALYSIS', 'x': 0.5, 'xanchor': 'center'},  width=875,
                                            xaxis_title='Category',
                                            yaxis_title='Amount',
                                            xaxis=dict(tickfont=dict(size=9.2)),                                  
                                            )
                    
                    fig2.update_xaxes(tickangle=90)

                    st.plotly_chart(fig2)
                
                with tab7:
                    st.table(top_payments) 

                    if st.button("Download Payment CSV"):
                        csv_data = frequent_payment_account.to_csv(index=False, encoding='utf-8')
                        b64 = base64.b64encode(csv_data.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="top_payments_mpesastatement.csv">Download CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)   
                

        with tab3:
            
            st.table(finaldf)

            # Add a button to download the filtered data as a CSV
            if st.button("Download CSV"):
                csv_data = finaldf.to_csv(index=False, encoding='utf-8')
                b64 = base64.b64encode(csv_data.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="mpesastatement.csv">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)  
        













    
