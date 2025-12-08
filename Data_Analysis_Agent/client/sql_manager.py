import pyodbc
from config import SERVER, DB_NAME, USER, PASSWORD

class SQLServerClient:
    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.conn = None
        self.cursor = None
        
        self.conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"  # Critical for your local setup
        )

    def __enter__(self):
        """Allows use with the 'with' statement for auto-closing"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-disconnects when exiting the 'with' block"""
        self.disconnect()

    def connect(self):
        """1. Connect to SQL DB"""
        try:
            if not self.conn:
                self.conn = pyodbc.connect(self.conn_str)
                self.cursor = self.conn.cursor()
                print(f"✅ Connected to {self.database}")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            raise

    def disconnect(self):
        """4. Disconnect from SQL DB"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("🔌 Disconnected")

    def execute_query(self, query, params=None):
        """
        2. Execute Custom SQL (SELECT).
        Returns a list of dictionaries (one dict per row).
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # Fetch columns to make the result readable (Dict instead of Tuple)
            columns = [column[0] for column in self.cursor.description]
            results = []
            for row in self.cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        except Exception as e:
            print(f"❌ Query Error: {e}")
            return None

    def execute_non_query(self, query, params=None):
        """
        2. Execute Custom SQL (INSERT/UPDATE/DELETE).
        Returns the number of rows affected.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.conn.rollback() # Undo changes on error
            print(f"❌ Execution Error: {e}")
            return -1

    def execute_sp(self, sp_name, params=None):
        """
        3. Execute Stored Procedure.
        Returns: List[Dict] (if SP returns data), True (if success but no data), or Error String.
        """
        try:
            # Construct the execution string: "EXEC sp_Name ?, ?"
            if params:
                placeholders = ', '.join(['?'] * len(params))
                sql = f"EXEC {sp_name} {placeholders}"
                self.cursor.execute(sql, params)
            else:
                sql = f"EXEC {sp_name}"
                self.cursor.execute(sql)
            
            # CHECK: Does this SP return data?
            if self.cursor.description:
                # Yes, fetch columns and rows
                columns = [column[0] for column in self.cursor.description]
                results = []
                for row in self.cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                # No, it was likely an action (INSERT/UPDATE/Process)
                self.conn.commit()
                print(f"✅ SP '{sp_name}' executed successfully (No data returned).")
                return True
                
        except Exception as e:
            error_msg = f"❌ SP Error in '{sp_name}': {e}"
            print(error_msg)
            return error_msg # Return the error text so the Agent knows what happened
        
if __name__ == "__main__":

    try:
        with SQLServerClient(SERVER, DB_NAME, USER, PASSWORD) as db:

            # --- TEST 1: Execute Stored Procedure ---
            print("\n--- Running ETL Stored Procedure ---")
            db.execute_sp("dbo.sp_LoadSupermarketSales")

            # --- TEST 2: Execute Custom SQL (SELECT) ---
            print("\n--- Querying Data ---")
            sql = "SELECT TOP 3 Invoice_ID, Total, Customer_type FROM dbo.supermarket_sales WHERE Total > ?"
            data = db.execute_query(sql, params=[500])
            
            for row in data:
                print(row)

            # --- TEST 3: Execute Custom SQL (INSERT/UPDATE) ---
            print("\n--- Updating a Record ---")
            update_sql = "UPDATE dbo.supermarket_sales SET City = ? WHERE Invoice_ID = ?"
            rows_affected = db.execute_non_query(update_sql, params=['New York', '750-67-8428'])
            print(f"Rows Updated: {rows_affected}")

    except Exception as e:
        print(f"Script stopped due to error: {e}")