import time
import pandas as pd
from db_agent.client.az_sql import SQLQueryExecutor

def test_graph_latency():
    print("--- Starting Azure SQL Graph PoC ---")
    
    graph_query = """
    SELECT 
        Person1.Name AS Person, 
        Person2.Name AS Friend, 
        FriendShip.SinceYear
    FROM 
        POC_Person AS Person1, 
        POC_FriendOf AS FriendShip, 
        POC_Person AS Person2
    WHERE 
        MATCH(Person1-(FriendShip)->Person2);
    """

    with SQLQueryExecutor() as executor:
        # 1. Warm-up (Connect & Cache)
        print("1. Warming up connection...")
        executor.execute_query("SELECT 1") 

        # 2. Latency Test (10 Iterations)
        print("2. Running 10 Graph Queries...")
        latencies = []
        for i in range(10):
            start = time.time()
            df = executor.execute_query(graph_query)
            duration_ms = (time.time() - start) * 1000
            latencies.append(duration_ms)
            print(f"   Query {i+1}: {duration_ms:.2f} ms | Rows: {len(df)}")

        # 3. Results
        avg_latency = sum(latencies) / len(latencies)
        print(f"\n--- RESULTS ---")
        print(f"Average Latency: {avg_latency:.2f} ms")
        
        if avg_latency < 200:
            print("✅ SUCCESS: Latency is acceptable for Agentic Workflow.")
        else:
            print("⚠️ WARNING: Latency is high. Consider NetworkX.")

if __name__ == "__main__":
    test_graph_latency()