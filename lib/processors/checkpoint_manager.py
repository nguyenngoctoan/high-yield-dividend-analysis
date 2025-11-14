"""
Checkpoint Manager for Progress Tracking and Error Recovery

Provides automatic checkpointing and recovery for long-running batch operations.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages checkpoints for resumable batch processing.

    Features:
    - Automatic checkpoint creation
    - Progress recovery from checkpoints
    - Checkpoint expiration and cleanup
    - Multiple checkpoint types (price, dividend, company, etc.)
    """

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

    def save_checkpoint(self,
                       checkpoint_type: str,
                       data: Dict[str, Any],
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a checkpoint.

        Args:
            checkpoint_type: Type of checkpoint (e.g., 'prices', 'dividends')
            data: Checkpoint data to save
            metadata: Optional metadata (stats, timestamp, etc.)

        Returns:
            Checkpoint file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_type}_{timestamp}.json"

        checkpoint = {
            'type': checkpoint_type,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'data': data,
            'metadata': metadata or {}
        }

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2, default=str)

            logger.info(f"💾 Checkpoint saved: {checkpoint_file.name}")
            return str(checkpoint_file)

        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")
            return ""

    def load_checkpoint(self, checkpoint_type: str) -> Optional[Dict[str, Any]]:
        """
        Load the most recent checkpoint of a given type.

        Args:
            checkpoint_type: Type of checkpoint to load

        Returns:
            Checkpoint data or None if not found
        """
        # Find all checkpoints of this type
        pattern = f"{checkpoint_type}_*.json"
        checkpoints = sorted(self.checkpoint_dir.glob(pattern), reverse=True)

        if not checkpoints:
            logger.info(f"📝 No checkpoint found for {checkpoint_type}")
            return None

        # Load most recent
        checkpoint_file = checkpoints[0]

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            logger.info(f"📂 Loaded checkpoint: {checkpoint_file.name}")
            logger.info(f"   Created: {checkpoint.get('created_at')}")

            return checkpoint

        except Exception as e:
            logger.error(f"❌ Failed to load checkpoint: {e}")
            return None

    def get_processed_items(self, checkpoint_type: str) -> List[str]:
        """
        Get list of already processed items from checkpoint.

        Args:
            checkpoint_type: Type of checkpoint

        Returns:
            List of processed item identifiers
        """
        checkpoint = self.load_checkpoint(checkpoint_type)

        if not checkpoint:
            return []

        data = checkpoint.get('data', {})
        return data.get('processed_items', [])

    def save_progress(self,
                     checkpoint_type: str,
                     processed_items: List[str],
                     total_items: int,
                     stats: Optional[Dict[str, Any]] = None):
        """
        Save progress checkpoint.

        Args:
            checkpoint_type: Type of operation
            processed_items: List of processed items
            total_items: Total number of items
            stats: Optional processing statistics
        """
        progress_pct = (len(processed_items) / total_items * 100) if total_items > 0 else 0

        data = {
            'processed_items': processed_items,
            'total_items': total_items,
            'progress_pct': f"{progress_pct:.2f}%"
        }

        metadata = {
            'stats': stats or {},
            'items_processed': len(processed_items),
            'items_remaining': total_items - len(processed_items)
        }

        self.save_checkpoint(checkpoint_type, data, metadata)

        logger.info(
            f"💾 Progress checkpoint: {len(processed_items):,}/{total_items:,} items "
            f"({progress_pct:.1f}%)"
        )

    def resume_from_checkpoint(self,
                              checkpoint_type: str,
                              all_items: List[str]) -> List[str]:
        """
        Get list of items that still need processing.

        Args:
            checkpoint_type: Type of checkpoint
            all_items: Complete list of items to process

        Returns:
            List of remaining items (not yet processed)
        """
        processed = set(self.get_processed_items(checkpoint_type))

        if not processed:
            logger.info(f"📝 No checkpoint found - processing all {len(all_items):,} items")
            return all_items

        remaining = [item for item in all_items if item not in processed]

        logger.info(
            f"📂 Resuming from checkpoint: {len(processed):,} already processed, "
            f"{len(remaining):,} remaining"
        )

        return remaining

    def clear_checkpoints(self, checkpoint_type: Optional[str] = None, older_than_days: int = 7):
        """
        Clear old checkpoints.

        Args:
            checkpoint_type: Specific type to clear (None for all)
            older_than_days: Clear checkpoints older than this many days
        """
        pattern = f"{checkpoint_type}_*.json" if checkpoint_type else "*.json"
        checkpoints = self.checkpoint_dir.glob(pattern)

        cleared_count = 0
        cutoff_timestamp = datetime.now().timestamp() - (older_than_days * 86400)

        for checkpoint_file in checkpoints:
            # Check file age
            if checkpoint_file.stat().st_mtime < cutoff_timestamp:
                try:
                    checkpoint_file.unlink()
                    cleared_count += 1
                except Exception as e:
                    logger.warning(f"⚠️  Failed to delete {checkpoint_file.name}: {e}")

        if cleared_count > 0:
            logger.info(f"🧹 Cleared {cleared_count} old checkpoint(s)")

    def get_checkpoint_summary(self) -> Dict[str, Any]:
        """
        Get summary of all checkpoints.

        Returns:
            Summary dictionary with checkpoint info
        """
        checkpoints = list(self.checkpoint_dir.glob("*.json"))

        summary = {
            'total_checkpoints': len(checkpoints),
            'checkpoint_dir': str(self.checkpoint_dir),
            'by_type': {}
        }

        # Group by type
        for checkpoint_file in checkpoints:
            parts = checkpoint_file.stem.split('_')
            if len(parts) >= 2:
                checkpoint_type = parts[0]
                if checkpoint_type not in summary['by_type']:
                    summary['by_type'][checkpoint_type] = []

                summary['by_type'][checkpoint_type].append({
                    'file': checkpoint_file.name,
                    'size_kb': checkpoint_file.stat().st_size / 1024,
                    'modified': datetime.fromtimestamp(checkpoint_file.stat().st_mtime).isoformat()
                })

        return summary


class ProgressTracker:
    """
    Track and log progress for long-running operations.

    Features:
    - Progress percentage tracking
    - ETA calculation
    - Throughput monitoring
    - Checkpoint integration
    """

    def __init__(self,
                 total_items: int,
                 operation_name: str = "Processing",
                 checkpoint_interval: int = 100):
        """
        Initialize progress tracker.

        Args:
            total_items: Total number of items to process
            operation_name: Name of operation for logging
            checkpoint_interval: Save checkpoint every N items
        """
        self.total_items = total_items
        self.operation_name = operation_name
        self.checkpoint_interval = checkpoint_interval

        self.processed_items = 0
        self.start_time = datetime.now()
        self.checkpoint_manager = CheckpointManager()

    def update(self, items_processed: int = 1):
        """
        Update progress.

        Args:
            items_processed: Number of items processed in this update
        """
        self.processed_items += items_processed

        # Log progress at intervals
        if self.processed_items % 100 == 0 or self.processed_items == self.total_items:
            self._log_progress()

    def _log_progress(self):
        """Log current progress with ETA."""
        progress_pct = (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # Calculate ETA
        if self.processed_items > 0:
            avg_time_per_item = elapsed / self.processed_items
            remaining_items = self.total_items - self.processed_items
            eta_seconds = remaining_items * avg_time_per_item
            eta_minutes = eta_seconds / 60

            # Calculate throughput
            throughput = self.processed_items / elapsed if elapsed > 0 else 0

            logger.info(
                f"📊 {self.operation_name}: {self.processed_items:,}/{self.total_items:,} "
                f"({progress_pct:.1f}%) - "
                f"ETA: {eta_minutes:.1f}m - "
                f"Throughput: {throughput:.1f} items/sec"
            )
        else:
            logger.info(
                f"📊 {self.operation_name}: {self.processed_items:,}/{self.total_items:,} "
                f"({progress_pct:.1f}%)"
            )

    def complete(self):
        """Mark operation as complete and log final stats."""
        duration = (datetime.now() - self.start_time).total_seconds()
        throughput = self.processed_items / duration if duration > 0 else 0

        logger.info(
            f"✅ {self.operation_name} complete: {self.processed_items:,} items "
            f"in {duration:.1f}s ({throughput:.1f} items/sec)"
        )


# Export main classes
__all__ = ['CheckpointManager', 'ProgressTracker']
