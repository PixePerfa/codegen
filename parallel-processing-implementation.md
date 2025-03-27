# Parallel Processing Framework Implementation Plan

## Overview

This document outlines the detailed implementation plan for the parallel processing framework, which is a key component of the Codegen upgrade plan. The framework will enable Codegen to leverage multi-core systems for improved performance when processing large codebases.

## Goals

1. Improve parsing and analysis performance by at least 3x on multi-core systems
2. Maintain memory efficiency during parallel operations
3. Provide configurable parallelism to adapt to different hardware environments
4. Ensure thread safety for all critical operations
5. Implement intelligent work distribution for optimal resource utilization

## Architecture

### Core Components

#### 1. Task System

```
+------------------+     +------------------+     +------------------+
| TaskDefinition   |     | TaskScheduler    |     | TaskExecutor     |
|------------------|     |------------------|     |------------------|
| - task_id        |     | - queue          |     | - thread_pool    |
| - dependencies   |     | - schedule()     |     | - execute()      |
| - priority       |     | - cancel()       |     | - wait()         |
| - callable       |     | - wait_all()     |     | - shutdown()     |
| - state          |     | - get_status()   |     |                  |
+------------------+     +------------------+     +------------------+
          |                      |                        |
          |                      |                        |
          v                      v                        v
+------------------+     +------------------+     +------------------+
| TaskResult       |     | TaskQueue        |     | ThreadPool       |
|------------------|     |------------------|     |------------------|
| - task_id        |     | - priority_queue |     | - workers        |
| - status         |     | - push()         |     | - queue          |
| - result         |     | - pop()          |     | - submit()       |
| - error          |     | - peek()         |     | - resize()       |
+------------------+     +------------------+     +------------------+
```

#### 2. Work Distribution

```
+------------------+     +------------------+     +------------------+
| WorkItem         |     | WorkDistributor  |     | WorkerStats      |
|------------------|     |------------------|     |------------------|
| - item_id        |     | - strategy       |     | - worker_id      |
| - dependencies   |     | - distribute()   |     | - completed      |
| - estimated_cost |     | - balance()      |     | - pending        |
| - data           |     | - optimize()     |     | - avg_time       |
+------------------+     +------------------+     +------------------+
          |                      |                        |
          |                      |                        |
          v                      v                        v
+------------------+     +------------------+     +------------------+
| BatchProcessor   |     | DistStrategy     |     | LoadBalancer     |
|------------------|     |------------------|     |------------------|
| - batch_size     |     | - round_robin    |     | - threshold      |
| - process_batch()|     | - work_stealing  |     | - rebalance()    |
| - split_batch()  |     | - cost_based     |     | - detect_skew()  |
+------------------+     +------------------+     +------------------+
```

#### 3. Synchronization and State Management

```
+------------------+     +------------------+     +------------------+
| SharedState      |     | Barrier          |     | ResultCollector  |
|------------------|     |------------------|     |------------------|
| - data           |     | - count          |     | - results        |
| - lock           |     | - wait()         |     | - collect()      |
| - read()         |     | - release()      |     | - aggregate()    |
| - write()        |     | - reset()        |     | - summarize()    |
+------------------+     +------------------+     +------------------+
          |                      |                        |
          |                      |                        |
          v                      v                        v
+------------------+     +------------------+     +------------------+
| AtomicCounter    |     | PhaseManager     |     | ProgressTracker  |
|------------------|     |------------------|     |------------------|
| - value          |     | - phases         |     | - total          |
| - increment()    |     | - current_phase  |     | - completed      |
| - decrement()    |     | - advance()      |     | - update()       |
+------------------+     +------------------+     +------------------+
```

## Implementation Details

### 1. Task System Implementation

#### 1.1 Task Definition

```python
class TaskDefinition:
    """Defines a unit of work that can be executed in parallel."""
    
    def __init__(self, 
                 callable_fn, 
                 task_id=None, 
                 dependencies=None, 
                 priority=0):
        """
        Initialize a task definition.
        
        Args:
            callable_fn: The function to execute
            task_id: Unique identifier for the task
            dependencies: List of task IDs that must complete before this task
            priority: Execution priority (higher values = higher priority)
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.callable = callable_fn
        self.dependencies = dependencies or []
        self.priority = priority
        self.state = TaskState.PENDING
        
    def can_execute(self, completed_tasks):
        """Check if all dependencies are satisfied."""
        return all(dep in completed_tasks for dep in self.dependencies)
```

#### 1.2 Task Scheduler

```python
class TaskScheduler:
    """Schedules and manages task execution."""
    
    def __init__(self, num_workers=None, max_memory_percent=75):
        """
        Initialize the task scheduler.
        
        Args:
            num_workers: Number of worker threads (default: CPU count)
            max_memory_percent: Maximum memory usage percentage
        """
        self.num_workers = num_workers or os.cpu_count()
        self.max_memory_percent = max_memory_percent
        self.queue = TaskQueue()
        self.executor = TaskExecutor(self.num_workers)
        self.completed_tasks = set()
        self.results = {}
        self.lock = threading.RLock()
        
    def schedule(self, task):
        """Schedule a task for execution."""
        with self.lock:
            self.queue.push(task)
        self._process_queue()
        
    def schedule_batch(self, tasks):
        """Schedule multiple tasks at once."""
        with self.lock:
            for task in tasks:
                self.queue.push(task)
        self._process_queue()
        
    def _process_queue(self):
        """Process tasks in the queue that are ready to execute."""
        with self.lock:
            executable_tasks = []
            for _ in range(self.queue.size()):
                task = self.queue.peek()
                if task.can_execute(self.completed_tasks):
                    self.queue.pop()
                    executable_tasks.append(task)
                else:
                    # Skip this task and try the next one
                    self.queue.rotate()
                    
            for task in executable_tasks:
                self._submit_task(task)
                
    def _submit_task(self, task):
        """Submit a task to the executor."""
        future = self.executor.submit(self._task_wrapper, task)
        future.add_done_callback(self._task_completed)
        
    def _task_wrapper(self, task):
        """Wrapper around the task callable to handle exceptions."""
        try:
            result = task.callable()
            return TaskResult(task.task_id, TaskState.COMPLETED, result)
        except Exception as e:
            return TaskResult(task.task_id, TaskState.FAILED, error=e)
            
    def _task_completed(self, future):
        """Callback when a task completes."""
        try:
            result = future.result()
            with self.lock:
                self.completed_tasks.add(result.task_id)
                self.results[result.task_id] = result
                self._process_queue()  # Process more tasks
        except Exception as e:
            logger.error(f"Error in task completion callback: {e}")
            
    def wait_all(self):
        """Wait for all scheduled tasks to complete."""
        self.executor.wait()
        
    def shutdown(self):
        """Shutdown the scheduler and executor."""
        self.executor.shutdown()
```

#### 1.3 Thread Pool Implementation

```python
class ThreadPool:
    """Custom thread pool for executing tasks."""
    
    def __init__(self, num_workers):
        """
        Initialize the thread pool.
        
        Args:
            num_workers: Number of worker threads
        """
        self.num_workers = num_workers
        self.queue = queue.Queue()
        self.workers = []
        self.shutdown_flag = threading.Event()
        self._start_workers()
        
    def _start_workers(self):
        """Start worker threads."""
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            
    def _worker_loop(self):
        """Main worker thread loop."""
        while not self.shutdown_flag.is_set():
            try:
                task = self.queue.get(timeout=0.1)
                if task is None:  # Sentinel value
                    break
                    
                task.run()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
            finally:
                self.queue.task_done()
                
    def submit(self, task):
        """Submit a task to the thread pool."""
        if self.shutdown_flag.is_set():
            raise RuntimeError("ThreadPool is shutting down")
        self.queue.put(task)
        
    def resize(self, new_size):
        """Resize the thread pool."""
        if new_size == self.num_workers:
            return
            
        if new_size < self.num_workers:
            # Reduce the number of workers
            for _ in range(self.num_workers - new_size):
                self.queue.put(None)  # Add sentinel to stop worker
                
            # Wait for workers to exit
            for worker in self.workers[new_size:]:
                worker.join(timeout=1.0)
                
            self.workers = self.workers[:new_size]
        else:
            # Increase the number of workers
            for i in range(self.num_workers, new_size):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"Worker-{i}",
                    daemon=True
                )
                worker.start()
                self.workers.append(worker)
                
        self.num_workers = new_size
        
    def shutdown(self, wait=True):
        """Shutdown the thread pool."""
        self.shutdown_flag.set()
        
        # Add sentinel values to stop all workers
        for _ in range(len(self.workers)):
            self.queue.put(None)
            
        if wait:
            for worker in self.workers:
                worker.join(timeout=1.0)
```

### 2. Integration with Codegen

#### 2.1 Parallel File Processing

```python
class ParallelFileProcessor:
    """Process files in parallel using the task system."""
    
    def __init__(self, codebase, num_workers=None):
        """
        Initialize the parallel file processor.
        
        Args:
            codebase: The codebase to process
            num_workers: Number of worker threads
        """
        self.codebase = codebase
        self.scheduler = TaskScheduler(num_workers)
        
    def process_files(self, file_paths, processor_fn):
        """
        Process multiple files in parallel.
        
        Args:
            file_paths: List of file paths to process
            processor_fn: Function to apply to each file
        
        Returns:
            Dictionary mapping file paths to processing results
        """
        # Create tasks for each file
        for file_path in file_paths:
            task = TaskDefinition(
                lambda path=file_path: processor_fn(path),
                task_id=file_path
            )
            self.scheduler.schedule(task)
            
        # Wait for all tasks to complete
        self.scheduler.wait_all()
        
        # Collect and return results
        results = {}
        for file_path in file_paths:
            if file_path in self.scheduler.results:
                result = self.scheduler.results[file_path]
                if result.status == TaskState.COMPLETED:
                    results[file_path] = result.result
                else:
                    logger.error(f"Failed to process {file_path}: {result.error}")
                    
        return results
        
    def shutdown(self):
        """Shutdown the processor."""
        self.scheduler.shutdown()
```

#### 2.2 Integration with File Discovery

```python
def discover_files_parallel(codebase, root_dir, file_patterns, exclusion_patterns=None):
    """
    Discover files in parallel.
    
    Args:
        codebase: The codebase instance
        root_dir: Root directory to start discovery
        file_patterns: List of file patterns to include
        exclusion_patterns: List of patterns to exclude
        
    Returns:
        List of discovered file paths
    """
    exclusion_patterns = exclusion_patterns or []
    
    # Split directory traversal into top-level directories for parallelism
    top_dirs = [os.path.join(root_dir, d) for d in os.listdir(root_dir)
               if os.path.isdir(os.path.join(root_dir, d))]
    
    # Create processor
    processor = ParallelFileProcessor(codebase)
    
    # Define discovery function for each top directory
    def discover_in_dir(directory):
        discovered = []
        for root, _, files in os.walk(directory):
            # Check if this directory should be excluded
            if any(re.match(pattern, root) for pattern in exclusion_patterns):
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                # Check if file matches include patterns and not exclude patterns
                if (any(re.match(pattern, file) for pattern in file_patterns) and
                    not any(re.match(pattern, file_path) for pattern in exclusion_patterns)):
                    discovered.append(file_path)
        return discovered
    
    # Process directories in parallel
    results = processor.process_files(top_dirs, discover_in_dir)
    processor.shutdown()
    
    # Combine results
    all_files = []
    for files in results.values():
        all_files.extend(files)
        
    return all_files
```

#### 2.3 Integration with Parsing

```python
def parse_files_parallel(codebase, file_paths):
    """
    Parse multiple files in parallel.
    
    Args:
        codebase: The codebase instance
        file_paths: List of file paths to parse
        
    Returns:
        Dictionary mapping file paths to parsed ASTs
    """
    # Create processor
    processor = ParallelFileProcessor(codebase)
    
    # Define parsing function
    def parse_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_ext = os.path.splitext(file_path)[1]
        parser = get_parser_for_extension(file_ext)
        
        if parser is None:
            return None
            
        return parser.parse(content, file_path)
    
    # Parse files in parallel
    results = processor.process_files(file_paths, parse_file)
    processor.shutdown()
    
    return results
```

### 3. Configuration and Tuning

#### 3.1 Configuration Options

```python
class ParallelProcessingConfig:
    """Configuration for parallel processing."""
    
    def __init__(self):
        """Initialize with default values."""
        # Number of worker threads (None = use CPU count)
        self.num_workers = None
        
        # Maximum memory usage percentage
        self.max_memory_percent = 75
        
        # Batch size for processing
        self.batch_size = 100
        
        # Priority boost for critical path tasks
        self.critical_path_priority = 10
        
        # Enable work stealing between threads
        self.enable_work_stealing = True
        
        # Minimum task size for parallelization (smaller tasks run sequentially)
        self.min_task_size = 1
        
        # Maximum number of tasks in flight
        self.max_tasks_in_flight = 1000
        
    @classmethod
    def from_dict(cls, config_dict):
        """Create configuration from dictionary."""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
        
    def to_dict(self):
        """Convert configuration to dictionary."""
        return {
            key: getattr(self, key)
            for key in dir(self)
            if not key.startswith('_') and not callable(getattr(self, key))
        }
```

#### 3.2 Auto-tuning

```python
class ParallelAutoTuner:
    """Auto-tunes parallel processing parameters."""
    
    def __init__(self, codebase):
        """
        Initialize the auto-tuner.
        
        Args:
            codebase: The codebase instance
        """
        self.codebase = codebase
        self.config = ParallelProcessingConfig()
        self.metrics = {}
        
    def tune(self):
        """Auto-tune parameters based on system and codebase."""
        # Adjust workers based on CPU count and available memory
        cpu_count = os.cpu_count()
        available_memory = psutil.virtual_memory().available
        total_memory = psutil.virtual_memory().total
        
        # Start with CPU count
        self.config.num_workers = cpu_count
        
        # Adjust based on memory constraints
        memory_per_worker = 200 * 1024 * 1024  # 200MB per worker estimate
        max_workers_by_memory = available_memory // memory_per_worker
        
        # Take the minimum
        self.config.num_workers = min(self.config.num_workers, max_workers_by_memory)
        
        # Ensure at least one worker
        self.config.num_workers = max(1, self.config.num_workers)
        
        # Adjust batch size based on codebase size
        codebase_size = len(self.codebase.files)
        if codebase_size < 100:
            self.config.batch_size = 10
        elif codebase_size < 1000:
            self.config.batch_size = 50
        else:
            self.config.batch_size = 100
            
        # Adjust max tasks in flight
        self.config.max_tasks_in_flight = self.config.num_workers * 10
        
        return self.config
        
    def benchmark(self, file_sample_size=100):
        """Run benchmarks to optimize configuration."""
        # Sample files for benchmarking
        all_files = list(self.codebase.files.keys())
        sample_size = min(file_sample_size, len(all_files))
        sample_files = random.sample(all_files, sample_size)
        
        # Test different worker counts
        worker_counts = [1, 2, 4, 8, 16, os.cpu_count()]
        worker_counts = sorted(set(worker_counts))
        
        results = {}
        for workers in worker_counts:
            if workers > os.cpu_count():
                continue
                
            # Configure processor
            processor = ParallelFileProcessor(self.codebase, workers)
            
            # Benchmark parsing
            start_time = time.time()
            processor.process_files(sample_files, lambda f: self.codebase.parse_file(f))
            elapsed = time.time() - start_time
            
            results[workers] = elapsed
            processor.shutdown()
            
        # Find optimal worker count
        optimal_workers = min(results.items(), key=lambda x: x[1])[0]
        self.config.num_workers = optimal_workers
        
        return results
```

## Integration with Codebase Class

```python
class Codebase:
    """Enhanced Codebase class with parallel processing capabilities."""
    
    def __init__(self, root_dir, parallel=True, parallel_config=None):
        """
        Initialize the codebase.
        
        Args:
            root_dir: Root directory of the codebase
            parallel: Whether to enable parallel processing
            parallel_config: Configuration for parallel processing
        """
        self.root_dir = root_dir
        self.parallel = parallel
        
        # Initialize parallel processing
        if self.parallel:
            self.parallel_config = parallel_config or ParallelProcessingConfig()
            self.parallel_processor = ParallelFileProcessor(self, self.parallel_config.num_workers)
        else:
            self.parallel_processor = None
            
        # Initialize other components
        self.files = {}
        self.symbols = {}
        # ... other initialization ...
        
        # Discover and parse files
        self._discover_files()
        self._parse_files()
        
    def _discover_files(self):
        """Discover files in the codebase."""
        if self.parallel:
            file_patterns = ["*.py", "*.ts", "*.js", "*.tsx", "*.jsx"]
            exclusion_patterns = ["**/node_modules/**", "**/.git/**", "**/venv/**"]
            
            self.file_paths = discover_files_parallel(
                self, self.root_dir, file_patterns, exclusion_patterns
            )
        else:
            # Existing sequential implementation
            pass
            
    def _parse_files(self):
        """Parse all discovered files."""
        if self.parallel:
            parsed_files = parse_files_parallel(self, self.file_paths)
            
            # Process parsed results
            for file_path, ast in parsed_files.items():
                if ast is not None:
                    self.files[file_path] = File(file_path, ast, self)
        else:
            # Existing sequential implementation
            pass
            
    def auto_tune_parallel(self):
        """Auto-tune parallel processing parameters."""
        if not self.parallel:
            return
            
        tuner = ParallelAutoTuner(self)
        self.parallel_config = tuner.tune()
        
        # Update processor with new configuration
        if self.parallel_processor:
            self.parallel_processor.shutdown()
            
        self.parallel_processor = ParallelFileProcessor(
            self, self.parallel_config.num_workers
        )
        
        return self.parallel_config
```

## Testing Strategy

1. **Unit Tests**:
   - Test each component of the parallel framework in isolation
   - Verify correct behavior with different configurations
   - Test edge cases and error handling

2. **Integration Tests**:
   - Test integration with file discovery and parsing
   - Verify correct behavior with different codebase sizes
   - Test with different file types and structures

3. **Performance Tests**:
   - Benchmark against sequential implementation
   - Test scaling with different numbers of cores
   - Measure memory usage during parallel operations

4. **Stress Tests**:
   - Test with very large codebases
   - Test with limited system resources
   - Test recovery from failures

## Deployment Plan

1. **Phase 1: Implementation**
   - Implement core task system
   - Implement thread pool and work distribution
   - Implement integration with file discovery and parsing

2. **Phase 2: Testing**
   - Run unit and integration tests
   - Perform performance benchmarks
   - Address any issues discovered

3. **Phase 3: Documentation**
   - Document API and configuration options
   - Create usage examples
   - Update architecture documentation

4. **Phase 4: Rollout**
   - Release as opt-in feature
   - Gather feedback from early adopters
   - Make adjustments based on real-world usage

## Conclusion

The parallel processing framework will significantly improve Codegen's performance on multi-core systems, particularly for large codebases. By implementing a flexible, configurable system with intelligent work distribution, we can achieve optimal resource utilization while maintaining the robustness and reliability expected from Codegen.

This implementation plan provides a detailed roadmap for developing the parallel processing framework, integrating it with the existing codebase, and ensuring it meets the performance and reliability goals of the Codegen upgrade plan.