"""
Performance Monitoring and Metrics Collection

Tracks and reports on system performance, API usage, and optimization effectiveness.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class APIMetrics:
    """API usage metrics."""
    endpoint: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    rate_limit_hits: int = 0

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        return self.total_response_time / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.successful_calls / self.total_calls * 100) if self.total_calls > 0 else 0.0

    def record_call(self, success: bool, response_time: float):
        """Record an API call."""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        self.total_response_time += response_time
        self.min_response_time = min(self.min_response_time, response_time)
        self.max_response_time = max(self.max_response_time, response_time)


@dataclass
class OptimizationMetrics:
    """Metrics for optimization effectiveness."""
    optimization_name: str
    items_processed: int = 0
    items_skipped: int = 0
    time_saved_seconds: float = 0.0
    api_calls_saved: int = 0
    enabled: bool = True

    @property
    def skip_rate(self) -> float:
        """Calculate percentage of items skipped."""
        total = self.items_processed + self.items_skipped
        return (self.items_skipped / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'optimization': self.optimization_name,
            'enabled': self.enabled,
            'items_processed': self.items_processed,
            'items_skipped': self.items_skipped,
            'skip_rate': f"{self.skip_rate:.1f}%",
            'time_saved_seconds': round(self.time_saved_seconds, 2),
            'api_calls_saved': self.api_calls_saved
        }


@dataclass
class PhaseMetrics:
    """Metrics for a processing phase."""
    phase_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    errors: List[str] = field(default_factory=list)

    def start(self):
        """Start timing this phase."""
        self.start_time = datetime.now()

    def complete(self):
        """Complete timing this phase."""
        self.end_time = datetime.now()

    @property
    def duration_seconds(self) -> float:
        """Get phase duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.items_successful / self.items_processed * 100) if self.items_processed > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'phase': self.phase_name,
            'duration_seconds': round(self.duration_seconds, 2),
            'items_processed': self.items_processed,
            'items_successful': self.items_successful,
            'items_failed': self.items_failed,
            'success_rate': f"{self.success_rate:.1f}%",
            'throughput': round(self.items_processed / self.duration_seconds, 2) if self.duration_seconds > 0 else 0
        }


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.

    Features:
    - API usage tracking
    - Optimization effectiveness monitoring
    - Phase timing and throughput
    - Performance reports and summaries
    """

    def __init__(self, metrics_dir: str = ".metrics"):
        """
        Initialize performance monitor.

        Args:
            metrics_dir: Directory to store metrics
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(exist_ok=True)

        # Metrics storage
        self.api_metrics: Dict[str, APIMetrics] = defaultdict(lambda: APIMetrics(endpoint="unknown"))
        self.optimization_metrics: Dict[str, OptimizationMetrics] = {}
        self.phase_metrics: Dict[str, PhaseMetrics] = {}

        # Overall timing
        self.run_start_time: Optional[datetime] = None
        self.run_end_time: Optional[datetime] = None

        # Counters
        self.total_api_calls = 0
        self.total_database_operations = 0

    def start_run(self):
        """Start timing the overall run."""
        self.run_start_time = datetime.now()
        logger.info(f"⏱️  Performance monitoring started at {self.run_start_time.strftime('%H:%M:%S')}")

    def complete_run(self):
        """Complete timing the overall run."""
        self.run_end_time = datetime.now()
        if self.run_start_time:
            duration = (self.run_end_time - self.run_start_time).total_seconds()
            logger.info(f"⏱️  Total execution time: {duration:.1f}s ({duration/60:.1f}m)")

    def record_api_call(self, endpoint: str, success: bool, response_time: float):
        """
        Record an API call.

        Args:
            endpoint: API endpoint name
            success: Whether the call succeeded
            response_time: Response time in seconds
        """
        if endpoint not in self.api_metrics:
            self.api_metrics[endpoint] = APIMetrics(endpoint=endpoint)

        self.api_metrics[endpoint].record_call(success, response_time)
        self.total_api_calls += 1

    def start_phase(self, phase_name: str):
        """
        Start timing a processing phase.

        Args:
            phase_name: Name of the phase
        """
        phase = PhaseMetrics(phase_name=phase_name)
        phase.start()
        self.phase_metrics[phase_name] = phase
        logger.info(f"📍 Starting phase: {phase_name}")

    def complete_phase(self, phase_name: str, items_processed: int = 0,
                      items_successful: int = 0, items_failed: int = 0):
        """
        Complete a processing phase.

        Args:
            phase_name: Name of the phase
            items_processed: Total items processed
            items_successful: Successful items
            items_failed: Failed items
        """
        if phase_name in self.phase_metrics:
            phase = self.phase_metrics[phase_name]
            phase.complete()
            phase.items_processed = items_processed
            phase.items_successful = items_successful
            phase.items_failed = items_failed

            logger.info(
                f"✅ Phase complete: {phase_name} - "
                f"{phase.duration_seconds:.1f}s, "
                f"{items_successful}/{items_processed} successful"
            )

    def record_optimization(self, name: str, items_processed: int = 0,
                          items_skipped: int = 0, time_saved: float = 0.0,
                          api_calls_saved: int = 0):
        """
        Record optimization metrics.

        Args:
            name: Optimization name
            items_processed: Items processed
            items_skipped: Items skipped by optimization
            time_saved: Estimated time saved (seconds)
            api_calls_saved: API calls saved
        """
        if name not in self.optimization_metrics:
            self.optimization_metrics[name] = OptimizationMetrics(optimization_name=name)

        opt = self.optimization_metrics[name]
        opt.items_processed += items_processed
        opt.items_skipped += items_skipped
        opt.time_saved_seconds += time_saved
        opt.api_calls_saved += api_calls_saved

        if items_skipped > 0:
            logger.info(
                f"⚡ {name}: Skipped {items_skipped:,} items "
                f"(saved ~{time_saved:.0f}s, {api_calls_saved:,} API calls)"
            )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.

        Returns:
            Summary dictionary
        """
        # Calculate total duration
        total_duration = 0.0
        if self.run_start_time and self.run_end_time:
            total_duration = (self.run_end_time - self.run_start_time).total_seconds()

        # API summary
        api_summary = {
            'total_calls': self.total_api_calls,
            'by_endpoint': {}
        }

        for endpoint, metrics in self.api_metrics.items():
            api_summary['by_endpoint'][endpoint] = {
                'calls': metrics.total_calls,
                'success_rate': f"{metrics.success_rate:.1f}%",
                'avg_response_time': f"{metrics.avg_response_time:.3f}s"
            }

        # Optimization summary
        optimization_summary = {
            'total_time_saved': sum(opt.time_saved_seconds for opt in self.optimization_metrics.values()),
            'total_api_calls_saved': sum(opt.api_calls_saved for opt in self.optimization_metrics.values()),
            'by_optimization': [opt.to_dict() for opt in self.optimization_metrics.values()]
        }

        # Phase summary
        phase_summary = {
            'phases': [phase.to_dict() for phase in self.phase_metrics.values()]
        }

        return {
            'run_summary': {
                'start_time': self.run_start_time.isoformat() if self.run_start_time else None,
                'end_time': self.run_end_time.isoformat() if self.run_end_time else None,
                'total_duration_seconds': round(total_duration, 2),
                'total_duration_minutes': round(total_duration / 60, 2)
            },
            'api_metrics': api_summary,
            'optimizations': optimization_summary,
            'phases': phase_summary
        }

    def save_metrics(self, filename: Optional[str] = None):
        """
        Save metrics to file.

        Args:
            filename: Optional filename (default: auto-generated with timestamp)
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"metrics_{timestamp}.json"

        filepath = self.metrics_dir / filename

        try:
            summary = self.get_summary()

            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2, default=str)

            logger.info(f"💾 Metrics saved: {filepath.name}")

        except Exception as e:
            logger.error(f"❌ Failed to save metrics: {e}")

    def print_summary(self):
        """Print performance summary to console."""
        summary = self.get_summary()

        print("\n" + "=" * 70)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 70)

        # Run summary
        run = summary['run_summary']
        print(f"\n⏱️  Execution Time: {run['total_duration_minutes']:.1f} minutes")

        # API metrics
        api = summary['api_metrics']
        print(f"\n📡 API Calls: {api['total_calls']:,} total")
        for endpoint, metrics in api['by_endpoint'].items():
            print(f"  • {endpoint}: {metrics['calls']:,} calls ({metrics['success_rate']} success)")

        # Optimizations
        opt = summary['optimizations']
        print(f"\n⚡ Optimizations:")
        print(f"  • Time saved: {opt['total_time_saved']:.0f}s ({opt['total_time_saved']/60:.1f}m)")
        print(f"  • API calls saved: {opt['total_api_calls_saved']:,}")

        for optimization in opt['by_optimization']:
            if optimization['items_skipped'] > 0:
                print(f"\n  {optimization['optimization']}:")
                print(f"    - Skipped: {optimization['items_skipped']:,} items ({optimization['skip_rate']})")
                print(f"    - Time saved: {optimization['time_saved_seconds']:.0f}s")
                print(f"    - API calls saved: {optimization['api_calls_saved']:,}")

        # Phases
        phases = summary['phases']['phases']
        if phases:
            print(f"\n📍 Phase Breakdown:")
            for phase in phases:
                print(f"\n  {phase['phase']}:")
                print(f"    - Duration: {phase['duration_seconds']:.1f}s")
                print(f"    - Processed: {phase['items_processed']:,} items")
                print(f"    - Success rate: {phase['success_rate']}")
                print(f"    - Throughput: {phase['throughput']:.1f} items/sec")

        print("\n" + "=" * 70)


# Export main class
__all__ = ['PerformanceMonitor', 'APIMetrics', 'OptimizationMetrics', 'PhaseMetrics']
