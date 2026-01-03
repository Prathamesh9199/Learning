import pyodbc
import pandas as pd
from db_agent.config import SQL_DATABASE, SQL_KEY, SQL_SERVER, SQL_USERNAME, ODBC_DRIVER

class SQLQueryExecutor:
    def __init__(self,
                 server=SQL_SERVER,
                 database=SQL_DATABASE,
                 username=SQL_USERNAME,
                 password=SQL_KEY,
                 driver=ODBC_DRIVER,
                 autocommit: bool = False,
                 ):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.autocommit = autocommit
        self.driver = driver
        self.conn = None
        self.cursor = None

    def _conn_string(self) -> str:
        return (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
        )

    def connect(self):
        if self.conn is None:
            self.conn = pyodbc.connect(self._conn_string(), autocommit=self.autocommit)
            self.cursor = self.conn.cursor()
        return self

    def close(self):
        if self.cursor:
            try:
                self.cursor.close()
            except Exception:
                pass
            self.cursor = None
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.close()

    def execute_query(self, query: str, fetch: bool = True):
        # Ensure a connection exists before executing
        self.connect() 

        try:
            if fetch:
                # Returns results as a DataFrame with proper column headers
                return pd.read_sql(query, self.conn)
            else:
                # For INSERT, UPDATE, DELETE, or stored procedures without returns
                self.cursor.execute(query)
                if not self.autocommit:
                    self.conn.commit()
                return None
        except Exception as e:
            # Rollback in case of an error to keep the transaction state clean
            if self.conn and not self.autocommit:
                self.conn.rollback()
            print(f"Error executing query: {e}")
            raise

    def check_connection(self):
        """Check if the connection is alive."""
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            return True
        except:
            return False

if __name__ == "__main__":
    with SQLQueryExecutor() as executor:
        query = """
            select top 2 *
            from SEMANTIC.COST_PER_PERSON_A
        """
        print("Executing query:", executor.execute_query(query))