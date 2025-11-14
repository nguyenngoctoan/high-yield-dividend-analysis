"""
Advanced Batch Processing Optimizer

Provides intelligent batching, chunking, and parallelization strategies
to maximize throughput while staying within rate limits.
"""

import logging
import time
from typing import List, Callable, Any, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BatchStats:
    """Statistics for batch processing."""
    total_items: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    throughput_items_per_sec: float = 0.0

    def start(self):
        """Start timing."""
        self.start_time = datetime.now()

    def complete(self):
        """Complete timing and calculate throughput."""
        self.end_time = datetime.now()
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds()
            if duration > 0:
                self.throughput_items_per_sec = self.processed / duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            'total_items': self.total_items,
            'processed': self.processed,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'duration_seconds': duration,
            'throughput_items_per_sec': self.throughput_items_per_sec,
            'success_rate': f"{(self.successful / self.processed * 100):.2f}%" if self.processed > 0 else "0%"
        }


class BatchOptimizer:
    """
    Advanced batch processing with intelligent chunking and rate limiting.

    Features:
    - Adaptive chunk sizing based on processing time
    - Rate limit aware batching
    - Automatic retry with exponential backoff
    - Progress checkpointing
    - Parallel processing with configurable workers
    """

    def __init__(self,
                 max_workers: int = 10,
                 rate_limit_per_min: int = 750,
                 chunk_size: int = 100,
                 adaptive_chunking: bool = True):
        """
        Initialize batch optimizer.

        Args:
            max_workers: Maximum parallel workers
            rate_limit_per_min: API rate limit per minute
            chunk_size: Initial chunk size
            adaptive_chunking: Automatically adjust chunk size based on performance
        """
        self.max_workers = max_workers
        self.rate_limit_per_min = rate_limit_per_min
        self.initial_chunk_size = chunk_size
        self.adaptive_chunking = adaptive_chunking

        # Calculate optimal delay between requests
        self.min_delay_between_requests = 60.0 / rate_limit_per_min if rate_limit_per_min > 0 else 0

        # Stats
        self.stats = BatchStats()

        # Checkpointing
        self.checkpoints: Dict[str, Any] = {}

    def _calculate_optimal_chunk_size(self,
                                     avg_processing_time: float,
                                     target_chunk_duration: float = 30.0) -> int:
        """
        Calculate optimal chunk size based on processing time.

        Args:
            avg_processing_time: Average time per item (seconds)
            target_chunk_duration: Target time for processing a chunk (seconds)

        Returns:
            Optimal chunk size
        """
        if avg_processing_time <= 0:
            return self.initial_chunk_size

        optimal_size = int(target_chunk_duration / avg_processing_time)

        # Keep within reasonable bounds
        return max(10, min(optimal_size, 500))

    def process_batch_with_chunking(self,
                                    items: List[Any],
                                    process_func: Callable[[Any], Tuple[bool, Any]],
                                    checkpoint_func: Optional[Callable[[List[Any]], None]] = None,
                                    chunk_name: str = "batch") -> Dict[str, Any]:
        """
        Process items in adaptive chunks with checkpointing.

        Args:
            items: List of items to process
            process_func: Function to process each item, returns (success: bool, result: Any)
            checkpoint_func: Optional function to call after each chunk
            chunk_name: Name for logging

        Returns:
            Processing statistics
        """
        self.stats = BatchStats()
        self.stats.total_items = len(items)
        self.stats.start()

        logger.info(f"📦 Starting batch processing: {len(items):,} items")
        logger.info(f"⚙️  Config: {self.max_workers} workers, {self.rate_limit_per_min} req/min limit")

        chunk_size = self.initial_chunk_size
        chunk_times = []

        # Process in chunks
        for chunk_start in range(0, len(items), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(items))
            chunk_items = items[chunk_start:chunk_end]
            chunk_num = chunk_start // chunk_size + 1
            total_chunks = (len(items) + chunk_size - 1) // chunk_size

            chunk_start_time = time.time()

            logger.info(f"📦 Processing chunk {chunk_num}/{total_chunks} ({len(chunk_items)} items)...")

            # Process chunk in parallel
            chunk_results = self._process_chunk_parallel(chunk_items, process_func)

            # Update stats
            for success, result in chunk_results:
                self.stats.processed += 1
                if success:
                    self.stats.successful += 1
                else:
                    self.stats.failed += 1
                    if isinstance(result, str):
                        self.stats.errors.append(result)

            chunk_duration = time.time() - chunk_start_time
            chunk_times.append(chunk_duration)

            logger.info(
                f"✅ Chunk {chunk_num}/{total_chunks} complete: "
                f"{self.stats.successful} successful, {self.stats.failed} failed "
                f"({chunk_duration:.1f}s)"
            )

            # Checkpoint
            if checkpoint_func:
                try:
                    checkpoint_func(chunk_items)
                except Exception as e:
                    logger.warning(f"⚠️  Checkpoint failed: {e}")

            # Adaptive chunk sizing
            if self.adaptive_chunking and len(chunk_times) >= 2:
                avg_chunk_time = sum(chunk_times[-5:]) / len(chunk_times[-5:])
                avg_item_time = avg_chunk_time / chunk_size

                new_chunk_size = self._calculate_optimal_chunk_size(avg_item_time)

                if new_chunk_size != chunk_size:
                    logger.info(f"⚡ Adaptive chunking: {chunk_size} → {new_chunk_size} items/chunk")
                    chunk_size = new_chunk_size

        self.stats.complete()

        logger.info(
            f"🎉 Batch complete: {self.stats.successful:,}/{self.stats.total_items:,} successful "
            f"({self.stats.throughput_items_per_sec:.1f} items/sec)"
        )

        return self.stats.to_dict()

    def _process_chunk_parallel(self,
                                items: List[Any],
                                process_func: Callable[[Any], Tuple[bool, Any]]) -> List[Tuple[bool, Any]]:
        """
        Process a chunk of items in parallel.

        Args:
            items: Items to process
            process_func: Processing function

        Returns:
            List of (success, result) tuples
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all items
            futures = {executor.submit(process_func, item): item for item in items}

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    success, result = future.result()
                    results.append((success, result))

                    # Rate limiting delay
                    if self.min_delay_between_requests > 0:
                        time.sleep(self.min_delay_between_requests)

                except Exception as e:
                    logger.error(f"❌ Processing error: {e}")
                    results.append((False, str(e)))

        return results

    def process_with_retry(self,
                          items: List[Any],
                          process_func: Callable[[Any], Tuple[bool, Any]],
                          max_retries: int = 3,
                          backoff_factor: float = 2.0) -> Dict[str, Any]:
        """
        Process items with automatic retry and exponential backoff.

        Args:
            items: Items to process
            process_func: Processing function
            max_retries: Maximum retry attempts per item
            backoff_factor: Exponential backoff multiplier

        Returns:
            Processing statistics
        """
        self.stats = BatchStats()
        self.stats.total_items = len(items)
        self.stats.start()

        failed_items = defaultdict(int)  # item -> retry count
        pending_items = items.copy()

        for retry_attempt in range(max_retries + 1):
            if not pending_items:
                break

            if retry_attempt > 0:
                logger.info(f"🔄 Retry attempt {retry_attempt}/{max_retries} for {len(pending_items)} items...")
                # Exponential backoff
                delay = backoff_factor ** (retry_attempt - 1)
                logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            # Process current batch
            results = self._process_chunk_parallel(pending_items, process_func)

            # Separate successes and failures
            next_pending = []
            for i, (success, result) in enumerate(results):
                item = pending_items[i]
                self.stats.processed += 1

                if success:
                    self.stats.successful += 1
                else:
                    failed_items[str(item)] += 1
                    if failed_items[str(item)] < max_retries:
                        next_pending.append(item)
                    else:
                        self.stats.failed += 1
                        self.stats.errors.append(f"{item}: {result}")

            pending_items = next_pending

        self.stats.complete()

        logger.info(
            f"✅ Processing complete: {self.stats.successful:,} successful, "
            f"{self.stats.failed:,} failed after {max_retries} retries"
        )

        return self.stats.to_dict()


class SmartBatcher:
    """
    Smart batching utility for grouping items by optimal batch size.

    Features:
    - Automatic batch size calculation based on API limits
    - Symbol grouping by exchange or other criteria
    - Memory-efficient batch generation
    """

    @staticmethod
    def create_batches(items: List[Any],
                      batch_size: int = 100,
                      group_by: Optional[Callable[[Any], str]] = None) -> List[List[Any]]:
        """
        Create batches from items.

        Args:
            items: Items to batch
            batch_size: Maximum batch size
            group_by: Optional function to group items (e.g., by exchange)

        Returns:
            List of batches
        """
        if not items:
            return []

        if group_by is None:
            # Simple batching
            return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

        # Group by criteria first
        groups = defaultdict(list)
        for item in items:
            key = group_by(item)
            groups[key].append(item)

        # Create batches within each group
        all_batches = []
        for group_items in groups.values():
            group_batches = [group_items[i:i + batch_size]
                           for i in range(0, len(group_items), batch_size)]
            all_batches.extend(group_batches)

        return all_batches

    @staticmethod
    def calculate_optimal_batch_size(total_items: int,
                                    rate_limit_per_min: int,
                                    target_duration_min: int = 60,
                                    max_batch_size: int = 500) -> int:
        """
        Calculate optimal batch size based on constraints.

        Args:
            total_items: Total number of items to process
            rate_limit_per_min: API rate limit per minute
            target_duration_min: Target completion time in minutes
            max_batch_size: Maximum allowed batch size

        Returns:
            Optimal batch size
        """
        # Calculate items per minute needed to meet target
        items_per_min = total_items / target_duration_min

        # Ensure we don't exceed rate limit
        items_per_min = min(items_per_min, rate_limit_per_min)

        # Calculate batch size (process in 1-minute chunks)
        optimal_size = int(items_per_min)

        # Keep within bounds
        return max(10, min(optimal_size, max_batch_size))


# Export main classes
__all__ = ['BatchOptimizer', 'SmartBatcher', 'BatchStats']
