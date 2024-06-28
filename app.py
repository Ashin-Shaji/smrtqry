import streamlit as st
import sqlite3
import pandas as pd
import os
import google.generativeai as genai

# Function to connect to the SQLite database
def create_conn(db_name):
    if not os.path.exists(f'{db_name}.db'):
        return None
    conn = sqlite3.connect(f'{db_name}.db')
    return conn

# Function to create a new database connection if the database does not exist
def create_new_db(db_name):
    conn = sqlite3.connect(f'{db_name}.db')
    return conn

#get schema of the table
def get_table_schema(database_file, table_name):
    conn = sqlite3.connect(database_file)
    cursor = conn.execute(f"PRAGMA table_info({table_name})")

    schema_dict = {}
    for row in cursor.fetchall():
        column_name, data_type, _, _, _, _ = row
        schema_dict[column_name] = data_type

    conn.close()
    return schema_dict

# Function to check if a table exists
def check_table_exists(conn, table):
    c = conn.cursor()
    c.execute(f'''
        SELECT count(name)
        FROM sqlite_master
        WHERE type='table' AND name='{table}'
    ''')
    return c.fetchone()[0] == 1

# Function to create a table in the database
def create_tbl(table, conn):
    c = conn.cursor()
    c.execute(f'''
        CREATE TABLE {table} (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL
        )
    ''')
    conn.commit()

# Function to create a new employee in the database
def create_employee(table, conn, name_val, pos_val, hire_val, deprt_val, sal_val):
    c = conn.cursor()
    c.execute(f"INSERT INTO {table} (name, position, hire_date, department, salary) VALUES ('{name_val}', '{pos_val}', '{hire_val}', '{deprt_val}', {sal_val})")
    conn.commit()

def get_palm_response(text, prompt):
    global response
    try:
        os.environ['GOOGLE_API_KEY'] = 'AIzaSyB5JjP_KNtiZAfB48zB3b4-qQa1XQqb70k'  # Replace with your API key
        genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

        models = [m for m in genai.list_models() if "text-bison" in m.name]
        model = models[0].name

        # Generate text using the specified model
        completion = genai.generate_text(
            model=model,
            prompt=text + prompt,
            temperature=0.0,
            max_output_tokens=800)

        output = completion.result.split('\n')
        response = "\n".join(output)
        return response
    except Exception as e:
        print(f"An error occurred in the get_palm_response function: {str(e)}")
        return None

# Streamlit UI
# Initialize session state for connection and tables
if "conn" not in st.session_state:
    st.session_state.conn = None

if "tables" not in st.session_state:
    st.session_state.tables = []
    
# Streamlit UI
st.markdown(f"<h2 style='color:indigo;'>{'SQLite Database Explorer and Data Entry'}</h2>",unsafe_allow_html = True)
# UI for Database Name
# db_name = st.text_input("Enter Database Name", value='database')
# connect_button = st.button("Create/Connect to Database")

# # Handle Database Connection
# if connect_button and db_name:
#     st.session_state.conn = create_conn(db_name)
#     if st.session_state.conn is None:
#         st.warning("Database does not exist. Creating a new database.")
#         st.session_state.conn = create_new_db(db_name)
#     else:
#         st.success("Database exists and connected successfully.")

#     if st.session_state.conn:
#         c = st.session_state.conn.cursor()
#         c.execute("SELECT name FROM sqlite_master WHERE type='table';")
#         st.session_state.tables = [table[0] for table in c.fetchall()]

# if st.session_state.conn:
#     with st.form("employee_form"):
#         st.markdown(f"<h3 style='color:brown;'>{'Enter employee details:'}</h3>", unsafe_allow_html=True)
#         tbl_name = st.text_input("Enter New Table Name (or leave blank to select existing)")
#         existing_tbl_name = st.selectbox("Or Select Existing Table", [""] + st.session_state.tables)
#         name_val = st.text_input("Name")
#         pos_val = st.text_input("Position")
#         hire_val = st.date_input("Hire Date")
#         deprt_val = st.text_input("Department")
#         sal_val = st.number_input("Salary", min_value=0.0, step=1000.0)
#         submit_button = st.form_submit_button("Submit")

#         if submit_button:
#             table_to_use = tbl_name if tbl_name else existing_tbl_name
#             if not table_to_use:
#                 st.error("Please provide a table name or select an existing table.")
#             else:
#                 if not check_table_exists(st.session_state.conn, table_to_use):
#                     create_tbl(table_to_use, st.session_state.conn)
#                     st.info(f"Table '{table_to_use}' did not exist and has been created.")
#                 create_employee(table_to_use, st.session_state.conn, name_val, pos_val, str(hire_val), deprt_val, sal_val)
#                 st.success("Employee data added successfully!")
#                 # Refresh the tables list
#                 c = st.session_state.conn.cursor()
#                 c.execute("SELECT name FROM sqlite_master WHERE type='table';")
#                 st.session_state.tables = [table[0] for table in c.fetchall()]

#     with st.expander("Show All Tables"):
#         for table in st.session_state.tables:
#             st.write(table)

#     table_name = st.selectbox("Select Table Name to View Data", st.session_state.tables, index=0)

#     if table_name:
#         with st.expander("Show Table Data"):
#             try:
#                 df = pd.read_sql_query(f"SELECT * FROM {table_name}", st.session_state.conn)
#                 st.dataframe(df)
#             except Exception as e:
#                 st.error(f"Error retrieving data from table '{table_name}': {e}")

#         # LLM Interaction Section
#         st.markdown(f"<h3 style=color:brown;'>{'Generate SQL Query using LLM'}</h3>", unsafe_allow_html=True)
#         query_prompt = st.text_area("Enter your query prompt", "")
#         if st.button("Generate SQL Query"):
#             db_name = f'{db_name}.db'
#             schema_info = get_table_schema(db_name, table_name)
#             prompt = f"your only task is to just give only the proper clean sql query after understanding the input without giving unnecessary keywords, use the following schema data(having all existing column names) \n '{schema_info}' of the table named '{table_name}' to create proper sql queries"
#             palm_response = get_palm_response(query_prompt, prompt)
#             st.write("Generated SQL Query:")
#             st.code(palm_response)
#             try:
#                 result_df = pd.read_sql_query(palm_response, st.session_state.conn)
#                 st.write("Query Result:")
#                 st.dataframe(result_df)
#                 prompt2 = f'based on this query:\n "{query_prompt}" from the user, and this result "{result_df}" make a sentence to display the respective answer from this data'
#                 palm_response2 = get_palm_response(result_df.to_string(), prompt2)
#                 st.markdown(f'<span style="color:BlueViolet;">{palm_response2}</span>', unsafe_allow_html=True)
#             except Exception as e:
#                 st.error(f"Error executing generated query: {e}")

#         # Direct SQL Query Section
#         st.markdown(f"<h3 style=color:brown>{'Direct SQL Query'}</h3>", unsafe_allow_html=True)
#         direct_query = st.text_area("Enter your SQL query", "")
#         if st.button("Execute SQL Query"):
#             try:
#                 direct_df = pd.read_sql_query(direct_query, st.session_state.conn)
#                 st.write("Query Result:")
#                 st.dataframe(direct_df)
#             except Exception as e:
#                 st.error(f"Error executing query: {e}")


# UI for Database Name
db_name = st.text_input("Enter Database Name", value='database')
connect_button = st.button("Create/Connect to Database")

# Handle Database Connection
conn = None
tables = []

if connect_button and db_name:
    conn = create_conn(db_name)
    if conn is None:
        st.warning("Database does not exist. Creating a new database.")
        conn = create_new_db(db_name)
    else:
        st.success("Database exists and connected successfully.")

    if conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in c.fetchall()]

if conn:
    with st.form("employee_form"):
        st.markdown(f"<h3 style='color:brown;'>{'Enter employee details:'}</h3>", unsafe_allow_html=True)
        tbl_name = st.text_input("Enter New Table Name (or leave blank to select existing)")
        existing_tbl_name = st.selectbox("Or Select Existing Table", [""] + tables)
        name_val = st.text_input("Name")
        pos_val = st.text_input("Position")
        hire_val = st.date_input("Hire Date")
        deprt_val = st.text_input("Department")
        sal_val = st.number_input("Salary", min_value=0.0, step=1000.0)
        submit_button = st.form_submit_button("Submit")

        if submit_button:
            table_to_use = tbl_name if tbl_name else existing_tbl_name
            if not table_to_use:
                st.error("Please provide a table name or select an existing table.")
            else:
                if not check_table_exists(conn, table_to_use):
                    create_tbl(table_to_use, conn)
                    st.info(f"Table '{table_to_use}' did not exist and has been created.")
                create_employee(table_to_use, conn, name_val, pos_val, str(hire_val), deprt_val, sal_val)
                st.success("Employee data added successfully!")
                # Refresh the tables list
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [table[0] for table in c.fetchall()]

    with st.expander("Show All Tables"):
        for table in tables:
            st.write(table)

    table_name = st.selectbox("Select Table Name to View Data", tables, index=0)

    if table_name:
        with st.expander("Show Table Data"):
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error retrieving data from table '{table_name}': {e}")

        # LLM Interaction Section
        st.markdown(f"<h3 style=color:brown;'>{'Generate SQL Query using LLM'}</h3>", unsafe_allow_html=True)
        query_prompt = st.text_area("Enter your query prompt", "")
        if st.button("Generate SQL Query"):
            db_name = f'{db_name}.db'
            schema_info = get_table_schema(db_name, table_name)
            prompt = f"your only task is to just give only the proper clean sql query after understanding the input without giving unnecessary keywords, use the following schema data(having all existing column names) \n '{schema_info}' of the table named '{table_name}' to create proper sql queries"
            palm_response = get_palm_response(query_prompt, prompt)
            st.write("Generated SQL Query:")
            st.code(palm_response)
            try:
                result_df = pd.read_sql_query(palm_response, conn)
                st.write("Query Result:")
                st.dataframe(result_df)
                prompt2 = f'based on this query:\n "{query_prompt}" from the user, and this result "{result_df}" make a sentence to display the respective answer from this data'
                palm_response2 = get_palm_response(result_df.to_string(), prompt2)
                st.markdown(f'<span style="color:BlueViolet;">{palm_response2}</span>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error executing generated query: {e}")

        # Direct SQL Query Section
        st.markdown(f"<h3 style=color:brown>{'Direct SQL Query'}</h3>", unsafe_allow_html=True)
        direct_query = st.text_area("Enter your SQL query", "")
        if st.button("Execute SQL Query"):
            try:
                direct_df = pd.read_sql_query(direct_query, conn)
                st.write("Query Result:")
                st.dataframe(direct_df)
            except Exception as e:
                st.error(f"Error executing query: {e}")
