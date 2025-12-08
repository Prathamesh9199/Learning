from typing import Any, Dict, Callable, Optional, List
from pydantic import create_model, Field
from resources.registry.sql_sp import SP_REGISTRY
from client.sql_manager import SQLServerClient
from config import SERVER, DB_NAME, USER, PASSWORD

def get_db_client():
    """Factory to get a fresh DB connection"""
    return SQLServerClient(SERVER, DB_NAME, USER, PASSWORD)

def create_sp_tool(sp_name: str, sp_meta: Any) -> Callable:
    """
    Creates a Python function that wraps the SQL Execution.
    The function signature is dynamically typed based on SP_REGISTRY.
    """
    
    # 1. Dynamic Pydantic Model for Arguments
    fields = {}
    for param_name, param_detail in sp_meta.parameters.items():
        # We default to Optional[str] to allow flexibility, 
        # but prompt engineering should encourage correct types.
        fields[param_name] = (Optional[str], Field(default=None, description=param_detail.description))
    
    # (Optional) We could register this InputModel if we were using PydanticAI's @tool properly,
    # but for dynamic function generation, we rely on the docstring/signature below.

    # 2. The actual function to execute
    def sp_wrapper(**kwargs):
        """
        Executes the stored procedure with provided arguments.
        """
        print(f"🛠️ Tool Execution: {sp_name} | Args: {kwargs}")
        
        try:
            with get_db_client() as db:
                # Construct params list based on registry order
                params = []
                for p_name in sp_meta.parameters.keys():
                    val = kwargs.get(p_name)
                    # Convert 'None' strings to actual None if LLM sends them
                    if val == "None" or val == "": 
                        val = None
                    params.append(val)
                
                # Execute utilizing the updated logic in sql_manager
                results = db.execute_sp(sp_name, params=params)
                
                # Handling the output
                if isinstance(results, str) and "Error" in results:
                    return results # Return error message directly
                
                if isinstance(results, list):
                    # Data found
                    if not results:
                        return "Query executed successfully but returned no data (Empty Result)."
                    
                    # Constraint Check: Truncate to avoid context overflow
                    if len(results) > 50:
                        return f"Result truncated. First 50 rows: {results[:50]}"
                    
                    return results

                return "Action completed successfully."

        except Exception as e:
            return f"System Error executing {sp_name}: {str(e)}"

    # Attach metadata for LLM introspection
    sp_wrapper.__name__ = sp_name
    sp_wrapper.__doc__ = sp_meta.description
    
    return sp_wrapper

def get_all_tools():
    """
    Iterates registry and returns list of callable tools.
    """
    tools = []
    for sp_name, sp_meta in SP_REGISTRY.items():
        tool_func = create_sp_tool(sp_name, sp_meta)
        tools.append(tool_func)
    return tools