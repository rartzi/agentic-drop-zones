# Simple Multi-Processing Solution for Agentic Drop Zone

## Overview
Implement a queue-based async worker pool to parallelize Claude Code processing without blocking file detection.

## Core Principle
**Decouple detection from processing** - Observers detect and enqueue, workers process asynchronously.

## Architecture

```
File System Events
       ↓
[Observer Threads] → [Async Queue] → [Worker Pool] → Claude Code
                           ↑              ↓
                      Priority/FIFO    Concurrent
                                      Processing
```

## Implementation Plan

### Phase 1: Add Queue Infrastructure

#### 1.1 Create ProcessingQueue Class
```python
class ProcessingQueue:
    - asyncio.Queue with priority support
    - Track pending/processing/completed items
    - Handle backpressure (max queue size)
    - Simple FIFO with optional priority by zone
```

#### 1.2 Create WorkerPool Class
```python
class WorkerPool:
    - Fixed number of async workers (default: 3)
    - Each worker pulls from queue independently
    - Graceful shutdown on Ctrl+C
    - Error isolation per worker
```

### Phase 2: Modify Existing Components

#### 2.1 Update DropZoneHandler
- Change `process_file()` to `enqueue_file()`
- Simply add file + metadata to queue
- Return immediately (non-blocking)
- Log queue depth for monitoring

#### 2.2 Update Agents Class
- Keep existing methods unchanged
- Add new `process_from_queue()` method
- Maintains backward compatibility

#### 2.3 Update AgenticDropZone
- Initialize queue and worker pool on start
- Start workers before observers
- Cleanup workers on shutdown
- Add queue stats to status display

### Phase 3: Configuration

Add to `drops.yaml`:
```yaml
processing:
  max_workers: 3  # Number of concurrent Claude Code instances
  queue_size: 100  # Max items in queue before blocking
  timeout: 300  # Seconds before killing stuck process
```

## Key Design Decisions

### Why Async Workers Not Threads?
- Claude SDK already uses async/await
- Better resource utilization
- Easier cancellation and timeout handling
- Single event loop for all workers

### Why Not Subprocesses?
- Avoid spawning overhead
- Simpler state management
- Shared MCP server connections
- Better error propagation

### Queue Strategy
- **FIFO by default** - Simple and predictable
- **Optional priority** - By zone or file pattern
- **Backpressure** - Block new events if queue full
- **Persistence** - Optional queue state to survive crashes

## Benefits

1. **True Parallelism** - Process N files simultaneously
2. **Non-blocking Detection** - Never miss file events
3. **Resource Control** - Limit concurrent CC instances
4. **Graceful Degradation** - Queue absorbs bursts
5. **Simple to Implement** - ~200 lines of code change

## Migration Path

### Step 1: Minimal Change (Quick Win)
- Add queue between detection and processing
- Single worker initially (maintains current behavior)
- Test thoroughly

### Step 2: Enable Concurrency
- Increase workers to 3
- Monitor resource usage
- Tune based on workload

### Step 3: Advanced Features (Optional)
- Priority queues per zone
- Dynamic worker scaling
- Queue persistence
- Retry logic

## Error Handling

- **Worker Crash**: Restart worker, requeue item
- **CC Timeout**: Kill process, log error, continue
- **Queue Full**: Log warning, drop oldest item
- **Shutdown**: Drain queue gracefully

## Monitoring

Display in console:
```
📊 Processing Status:
   Queue: 5 pending | 3 processing
   Workers: 3/3 active
   Completed: 127 files
   Errors: 2
```

## Testing Strategy

1. **Burst Test**: Drop 20 files simultaneously
2. **Sustained Load**: 1 file/second for 5 minutes
3. **Error Recovery**: Kill worker mid-process
4. **Resource Limits**: Max out queue and workers

## Implementation Effort

- **Estimated LOC**: ~200 lines added/modified
- **Risk**: Low (queue pattern is well-understood)
- **Complexity**: Medium (async coordination)
- **Time**: 4-6 hours to implement and test

## Alternative Consideration

If this proves too complex, fallback to:
- Simple `asyncio.create_task()` without await
- No queue, just fire-and-forget
- Accept occasional resource exhaustion
- 50 lines of code change

## Success Criteria

✅ Can process 5+ files simultaneously
✅ File detection never blocked
✅ Graceful shutdown preserves queue state
✅ Clear visibility into processing status
✅ No more than 2x current code complexity