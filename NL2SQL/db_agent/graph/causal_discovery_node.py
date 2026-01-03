from typing import Dict, Any
from db_agent.graph.state import AgentState
from db_agent.client.az_sql import SQLQueryExecutor

def causal_discovery_node(state: AgentState) -> Dict[str, Any]:
    """
    Phase 4: Diagnostic Engine
    Queries the Knowledge Graph to generate a list of hypotheses.
    """
    print("--- [Node] Causal Discovery (The Graph) ---")
    current_buffer = state.get("stream_buffer", [])
    
    target_metric = "Cost" 
    print(f"   > Investigating drivers for: {target_metric}")

    # Streaming Update
    streaming_update = current_buffer + [f"Diagnostic: Querying Knowledge Graph for '{target_metric}' drivers..."]

    graph_query = f"""
    SELECT SourceNode.MappedColumn 
    FROM KG_Node AS SourceNode, KG_CausalLink AS Link, KG_Node AS TargetNode
    WHERE MATCH(SourceNode-(Link)->TargetNode)
    AND TargetNode.NodeName = '{target_metric}'
    """

    try:
        with SQLQueryExecutor() as executor:
            df = executor.execute_query(graph_query)
            if not df.empty:
                # Get the first column (MappedColumn)
                suspects = df.iloc[:, 0].tolist()
                suspects = [s for s in suspects if s]
                
                print(f"   > Graph found {len(suspects)} hypotheses (SQL Columns): {suspects}")
                
                return {
                    "hypotheses_queue": suspects,
                    "next_action": "PLAN",
                    "stream_buffer": streaming_update + [f"Diagnostic: Found {len(suspects)} hypotheses."]
                }
            else:
                print("   > Graph returned no leads.")
                return {
                    "hypotheses_queue": [], 
                    "next_action": "PLAN",
                    "stream_buffer": streaming_update + ["Diagnostic: No leads found in Graph."]
                }
                
    except Exception as e:
        print(f"   > Error querying Graph: {e}")
        return {
            "error_type": "GRAPH_ERROR", 
            "next_action": "FINALIZE",
            "stream_buffer": streaming_update + [f"Diagnostic: Graph Error - {e}"]
        }