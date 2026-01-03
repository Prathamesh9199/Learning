import json
from typing import Any, Optional, AsyncIterator, Dict, List, Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from db_agent.client.az_sql import SQLQueryExecutor

class SQLServerSaver(BaseCheckpointSaver):
    """
    Custom LangGraph Checkpointer that saves state to Azure SQL.
    Implements both Sync and Async interfaces.
    """
    
    def __init__(self, serde=None):
        super().__init__(serde=serde)

    # =========================================================
    # SYNCHRONOUS METHODS
    # =========================================================
    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Load the latest checkpoint for a given thread."""
        thread_id = config["configurable"]["thread_id"]
        
        query = f"""
        SELECT TOP 1 checkpoint_data, checkpoint_id, parent_checkpoint_id, metadata
        FROM agent_checkpoints
        WHERE thread_id = '{thread_id}'
        ORDER BY created_at DESC
        """
        
        with SQLQueryExecutor() as executor:
            df = executor.execute_query(query)
            
        if df.empty:
            return None
            
        row = df.iloc[0]
        
        # Parse JSON
        checkpoint = json.loads(row["checkpoint_data"])
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        parent_id = row["parent_checkpoint_id"]
        
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config={"configurable": {"thread_id": thread_id, "checkpoint_id": parent_id}} if parent_id else None
        )

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        """Save the current state to SQL."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]
        parent_id = config["configurable"].get("checkpoint_id")
        
        # Serialize
        data_str = json.dumps(checkpoint, default=str).replace("'", "''") 
        meta_str = json.dumps(metadata, default=str).replace("'", "''")
        
        # MERGE / UPSERT Query
        query = f"""
        MERGE INTO agent_checkpoints AS Target
        USING (SELECT '{thread_id}' AS thread_id, '{checkpoint_id}' AS checkpoint_id) AS Source
        ON (Target.thread_id = Source.thread_id AND Target.checkpoint_id = Source.checkpoint_id)
        WHEN NOT MATCHED THEN
            INSERT (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint_data, metadata)
            VALUES ('{thread_id}', '{checkpoint_id}', 
                    {'NULL' if not parent_id else f"'{parent_id}'"}, 
                    '{data_str}', '{meta_str}');
        """
        
        with SQLQueryExecutor() as executor:
            executor.execute_query(query, fetch=False)
            
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            }
        }

    def put_writes(self, config: RunnableConfig, writes: List[Tuple[str, Any]], task_id: str) -> None:
        """Store intermediate writes. (Not used in this MVP, but required by interface)."""
        pass

    def list(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None):
        """Not implemented for MVP."""
        return []

    # =========================================================
    # ASYNCHRONOUS METHODS (Required for app.ainvoke)
    # =========================================================
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Async wrapper for get_tuple"""
        return self.get_tuple(config)

    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        """Async wrapper for put"""
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(self, config: RunnableConfig, writes: List[Tuple[str, Any]], task_id: str) -> None:
        """Async wrapper for put_writes"""
        return self.put_writes(config, writes, task_id)

    async def alist(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> AsyncIterator[CheckpointTuple]:
        """Async wrapper for list"""
        if False: yield