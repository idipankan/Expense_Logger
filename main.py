import streamlit as st
import duckdb
import uuid
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import pytz

# Connect to DuckDB or create the database
conn = duckdb.connect("expense.db")

# Create the table if it doesn't exist
conn.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    transaction_id TEXT,
    timestamp TIMESTAMP,
    expense_amt FLOAT,
    reason TEXT,
    expense_cat TEXT
);
''')

# Sidebar options
st.sidebar.header("Options")
option = st.sidebar.selectbox("Choose a feature", ["Log Expense", "View/Export Data", "Visualize Data","Update Data","Delete Data"])

# Function to get IST timestamp
def get_ist_time():
    ist = pytz.timezone("Asia/Kolkata")
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    ist_time = utc_now.astimezone(ist)
    return ist_time.replace(tzinfo=None)

if option == "Log Expense":
    st.header("Log a New Expense")
    expense_amt = st.number_input("Expense Amount (in INR)", step=1)
    reason = st.text_input("Reason for the expense")
    expense_cat = st.selectbox("Expense Category", ["Food", "Groceries", "Travel", "Utilities", "Leisure", "Others"])
    
    if st.button("Submit Expense"):
        timestamp = get_ist_time()
        conn.execute("INSERT INTO expenses VALUES (?, ?, ?, ?, ?)", (str(uuid.uuid4()), timestamp, expense_amt, reason, expense_cat))
        st.success("Expense logged successfully!")

elif option == "View/Export Data":
    st.header("View & Export Data")
    start_date = st.date_input("Start Date", value=datetime.now(pytz.timezone('Asia/Kolkata')) - timedelta(days=7))
    end_date = st.date_input("End Date", value=datetime.now(pytz.timezone('Asia/Kolkata')))
    
    if st.button("Export as CSV"):
        query = """
        SELECT transaction_id, timestamp AS Timestamp, expense_amt AS Expense_Amount, 
        reason as Reason, expense_cat as Expense_Category FROM expenses
        WHERE CAST(timestamp AS DATE) BETWEEN ? AND ?
        """
        data = conn.execute(query, (start_date, end_date)).fetchdf()
        if len(data) == 0:
            st.warning("No data found")
        else:
            st.dataframe(data)
            csv = data.to_csv(index=False)
            st.download_button("Download CSV", csv, "expenses.csv", "text/csv")

elif option == "Visualize Data":
    st.header("Visualize Data")
    start_date = st.date_input("Start Date", value=datetime.now(pytz.timezone('Asia/Kolkata')) - timedelta(days=7))
    end_date = st.date_input("End Date", value=datetime.now(pytz.timezone('Asia/Kolkata')))

    if st.button("Generate Visualization"):
        query = """
        SELECT CAST(timestamp AS DATE) as day, SUM(expense_amt) as total_expense
        FROM expenses
        WHERE CAST(timestamp AS DATE) BETWEEN ? AND ?
        GROUP BY day
        ORDER BY day
        """
        data = conn.execute(query, (start_date, end_date)).fetchdf()
        
        if not data.empty:
            chart = alt.Chart(data).mark_line().encode(
                x="day:T",
                y="total_expense:Q",
                tooltip=["day:T", "total_expense:Q"]
            ).properties(
                title="Daily Total Expenses"
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("No data available for the selected date range.")

elif option == "Update Data":

    id = st.text_input("Enter transaction ID")
    query = f"SELECT * FROM expenses where transaction_id = '{id}'"

    result = conn.execute(query).fetch_df()
    if len(result) != 0:
        st.dataframe(result)

    choice = st.selectbox(label="What field is to be updated?",options=["Expense Amount","Reason","Expense Category"])
    try:
        if choice == "Expense Amount":
            new_amt = st.number_input("Enter the new amount",step=0.1)
            if st.button("Update"):
                conn.execute(f"UPDATE expenses SET expense_amt = {new_amt} WHERE transaction_id = '{id}'")
                st.success("Updated!")
        elif choice == "Reason":
            new_reason = st.text_input("Enter the new reason")
            if st.button("Update"):
                conn.execute(f"UPDATE expenses SET reason = '{new_reason}' WHERE transaction_id = '{id}' ")
                st.success("Updated!")
        elif choice == "Expense Category":
            new_cat = st.selectbox("Expense Category", ["Food", "Groceries", "Travel", "Utilities", "Leisure", "Others"])
            if st.button("Update"):
                conn.execute(f"UPDATE expenses SET expense_cat = '{new_cat}' where transaction_id = '{id}' ")
                st.success("Updated!")
        
        
    except:
        st.error("There is some error")

elif option == "Delete Data":
    choice = st.selectbox(label="Pick a category",options=["Delete a transaction", "Delete between date range", "Delete All"])

    if choice == "Delete a transaction":
        id = st.text_input("Enter transaction ID")
        query = f"DELETE FROM expenses WHERE transaction_id = '{id}' "
        if st.button("Delete transaction"):
            try:
                conn.execute(query)
                st.success("Transaction deleted")
            except:
                st.error("Deletion failed")
    elif choice == "Delete between date range":
        lrange = st.date_input("Enter start date",value=datetime.now(pytz.timezone('Asia/Kolkata')))
        urange = st.date_input("Enter end date",value=datetime.now(pytz.timezone('Asia/Kolkata')))

        query = f"DELETE FROM expenses WHERE CAST(timestamp AS DATE) BETWEEN '{lrange}' AND '{urange}' "
        if st.button("Delete data"):
            try:
                conn.execute(query)
                st.success("Data deleted")
            except:
                st.error("Deletion failed")

    elif choice == "Delete All":
        st.warning("This will delete ALL data! Be careful.")
        query = "DELETE from expenses"
        if st.button("Delete data"):
            try:
                conn.execute(query)
                st.success("Data deleted")
            except:
                st.error("Deletion failed")
