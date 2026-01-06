"""Dual checkpointer: in-memory primary + SQLite backup.

Writes to both checkpointers on every save.
Reads from memory first (fast), falls back to SQLite (survives restarts).

This gives you:
- Fast checkpointing during a session (memory)
- Persistence across server restarts/reloads (SQLite backup)
- Manual control: delete SQLite DB to clear all checkpoints
"""

import logging
from typing import Any, AsyncIterator, Iterator, Optional, Sequence
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

logger = logging.getLogger(__name__)


class DualCheckpointer(BaseCheckpointSaver):
    """Checkpointer that writes to both memory and SQLite.

    Strategy:
    - PUT: Write to both memory AND SQLite
    - GET: Read from memory first, fall back to SQLite if not found
    - LIST: Combine results from both (memory preferred)

    This ensures:
    - Fast access during runtime (memory)
    - Survival across server restarts (SQLite)
    - Ability to manually clear by deleting SQLite DB
    """

    def __init__(self, memory: MemorySaver, sqlite: AsyncSqliteSaver):
        """Initialize dual checkpointer.

        Args:
            memory: In-memory checkpointer (fast, cleared on restart)
            sqlite: SQLite checkpointer (persistent, survives restarts)
        """
        super().__init__()
        self.memory = memory
        self.sqlite = sqlite
        logger.info("✅ Dual checkpointer initialized (memory + SQLite backup)")

    async def aput(
        self,
        config: dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, Any],
    ) -> dict[str, Any]:
        """Save checkpoint to BOTH memory and SQLite."""
        # Save to memory (fast)
        result = await self.memory.aput(config, checkpoint, metadata, new_versions)

        # Save to SQLite (backup)
        try:
            await self.sqlite.aput(config, checkpoint, metadata, new_versions)
            logger.debug("💾 Checkpoint saved to both memory and SQLite")
        except Exception as e:
            logger.warning(f"SQLite checkpoint save failed (memory saved): {e}")

        return result

    async def aput_writes(
        self,
        config: dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Save intermediate writes to BOTH memory and SQLite."""
        # Save to memory (fast)
        await self.memory.aput_writes(config, writes, task_id, task_path)

        # Save to SQLite (backup)
        try:
            await self.sqlite.aput_writes(config, writes, task_id, task_path)
            logger.debug("💾 Writes saved to both memory and SQLite")
        except Exception as e:
            logger.warning(f"SQLite writes save failed (memory saved): {e}")

    async def aget_tuple(self, config: dict[str, Any]) -> Optional[CheckpointTuple]:
        """Get checkpoint from memory first, fall back to SQLite."""
        # Try memory first (fast path)
        result = await self.memory.aget_tuple(config)
        if result:
            logger.debug("✅ Checkpoint loaded from memory")
            return result

        # Fall back to SQLite (restart recovery)
        try:
            result = await self.sqlite.aget_tuple(config)
            if result:
                logger.info("📦 Checkpoint restored from SQLite backup (after restart)")
                # Restore to memory for future fast access
                await self.memory.aput(
                    config,
                    result.checkpoint,
                    result.metadata,
                    {},  # No new versions on restore
                )
            return result
        except Exception as e:
            logger.warning(f"SQLite checkpoint load failed: {e}")
            return None

    async def alist(
        self,
        config: Optional[dict[str, Any]] = None,
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints from both sources (memory preferred)."""
        # Get from memory first
        seen_ids = set()
        async for checkpoint in self.memory.alist(
            config, filter=filter, before=before, limit=limit
        ):
            seen_ids.add(checkpoint.config["configurable"]["thread_id"])
            yield checkpoint

        # Add from SQLite if not in memory (e.g., after restart)
        try:
            async for checkpoint in self.sqlite.alist(
                config, filter=filter, before=before, limit=limit
            ):
                thread_id = checkpoint.config["configurable"]["thread_id"]
                if thread_id not in seen_ids:
                    logger.debug(
                        f"📦 Checkpoint {thread_id} found only in SQLite (restored)"
                    )
                    yield checkpoint
        except Exception as e:
            logger.warning(f"SQLite checkpoint list failed: {e}")

    # Synchronous versions (for compatibility)
    def put(
        self,
        config: dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, Any],
    ) -> dict[str, Any]:
        """Sync version - not used in async workflows."""
        raise NotImplementedError("Use async aput instead")

    def put_writes(
        self,
        config: dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Sync version - not used in async workflows."""
        raise NotImplementedError("Use async aput_writes instead")

    def get_tuple(self, config: dict[str, Any]) -> Optional[CheckpointTuple]:
        """Sync version - not used in async workflows."""
        raise NotImplementedError("Use async aget_tuple instead")

    def list(
        self,
        config: Optional[dict[str, Any]] = None,
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Sync version - not used in async workflows."""
        raise NotImplementedError("Use async alist instead")
