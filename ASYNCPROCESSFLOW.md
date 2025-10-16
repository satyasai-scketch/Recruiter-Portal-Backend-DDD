# Async CV Upload & Scoring Flow Implementation

## API Flow Architecture

### 1. Upload API Flow

```
POST /api/v1/candidate/upload-batch
├─> Validate files & persona
├─> Store CVs in storage (local/S3)
├─> Create database records
├─> Enqueue scoring job to RQ
└─> Return job_id immediately

GET /api/v1/jobs/{job_id}/status
└─> Return job status & results
```

### 2. Background Worker Flow

```
RQ Worker Process
├─> Dequeue scoring job
├─> Parse CV content (if needed)
├─> Call LLM scoring service
├─> Store scores in database
└─> Update job status
```

## Implementation Steps

### Step 1: Add RQ Dependencies

**File: `requirements.txt`**

- Add `rq>=1.16.2` (already present)
- Add `redis>=5.0.8` (already present)

### Step 2: Create Job Management Models

**New File: `app/db/models/job.py`**

```python
class JobModel(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)  # job_id
    type = Column(String, nullable=False)  # 'cv_scoring', 'cv_batch'
    status = Column(String, nullable=False)  # 'queued', 'processing', 'completed', 'failed'
    user_id = Column(String, ForeignKey("users.id"))
    persona_id = Column(String, nullable=True)
    candidate_ids = Column(JSON, nullable=True)  # List of candidate IDs
    cv_ids = Column(JSON, nullable=True)  # List of CV IDs
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
```

### Step 3: Create Alembic Migration

**File: `migrations/versions/{timestamp}_add_jobs_table.py`**

- Create jobs table with indexes on status, user_id, type

### Step 4: Create Job Schemas

**File: `app/schemas/job.py`**

```python
class JobStatus(BaseModel):
    job_id: str
    type: str
    status: str  # queued, processing, completed, failed
    persona_id: Optional[str]
    candidate_ids: Optional[List[str]]
    progress: Optional[dict]  # {processed: 5, total: 10}
    result: Optional[dict]
    error: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    message: str
```

### Step 5: Create RQ Task Definitions

**New File: `app/workers/tasks.py`**

```python
from rq import get_current_job
from app.db.session import get_session
from app.repositories.job_repo import SQLAlchemyJobRepository

def score_candidates_task(job_id: str, persona_id: str, cv_ids: List[str]):
    """Background task to score candidates against persona using LLM"""
    job = get_current_job()
    db = get_session()
    job_repo = SQLAlchemyJobRepository()
    
    try:
        # Update job status to processing
        job_repo.update_status(db, job_id, 'processing')
        
        # Process CVs in batches
        batch_size = 5
        total = len(cv_ids)
        results = []
        
        for i in range(0, total, batch_size):
            batch = cv_ids[i:i+batch_size]
            
            # Call LLM scoring service (teammate's implementation)
            # This would be: ScoringService().score_cvs_against_persona(batch, persona_id)
            batch_results = process_cv_batch(batch, persona_id, db)
            results.extend(batch_results)
            
            # Update progress
            progress = {'processed': min(i+batch_size, total), 'total': total}
            job_repo.update_progress(db, job_id, progress)
        
        # Update job as completed
        job_repo.complete_job(db, job_id, {'scores': results})
        
    except Exception as e:
        job_repo.fail_job(db, job_id, str(e))
    finally:
        db.close()
```

### Step 6: Create RQ Connection Manager

**New File: `app/workers/queue.py`**

```python
from redis import Redis
from rq import Queue
from app.core.config import settings

def get_redis_connection():
    return Redis.from_url(settings.redis_url)

def get_queue(name='default'):
    return Queue(name, connection=get_redis_connection())

def enqueue_scoring_job(persona_id: str, cv_ids: List[str], job_id: str):
    queue = get_queue('scoring')
    job = queue.enqueue(
        'app.workers.tasks.score_candidates_task',
        job_id=job_id,
        persona_id=persona_id,
        cv_ids=cv_ids,
        job_timeout='30m'
    )
    return job.id
```

### Step 7: Create Job Repository

**New File: `app/repositories/job_repo.py`**

```python
class JobRepository:
    def create_job(self, db: Session, job: JobModel) -> JobModel
    def get_job(self, db: Session, job_id: str) -> JobModel
    def update_status(self, db: Session, job_id: str, status: str)
    def update_progress(self, db: Session, job_id: str, progress: dict)
    def complete_job(self, db: Session, job_id: str, result: dict)
    def fail_job(self, db: Session, job_id: str, error: str)
    def list_user_jobs(self, db: Session, user_id: str, limit: int = 20)
```

### Step 8: Update Upload API Endpoint

**File: `app/api/v1/candidate.py`**

Add new endpoint:

```python
@router.post("/upload-batch", response_model=JobCreateResponse)
async def upload_cv_batch_with_scoring(
    files: List[UploadFile] = File(...),
    persona_id: str = Form(...),
    db: Session = Depends(db_session),
    user=Depends(get_current_user)
):
    # 1. Validate persona exists
    # 2. Upload files to storage
    # 3. Create candidate & CV records
    # 4. Create job record
    # 5. Enqueue scoring task
    # 6. Return job_id immediately
```

### Step 9: Create Job Status API

**New File: `app/api/v1/jobs.py`**

```python
@router.get("/{job_id}/status", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    db: Session = Depends(db_session),
    user=Depends(get_current_user)
):
    # Return job status and results if completed

@router.get("/my-jobs", response_model=List[JobStatus])
async def list_my_jobs(
    limit: int = 20,
    db: Session = Depends(db_session),
    user=Depends(get_current_user)
):
    # List user's jobs with pagination
```

### Step 10: Register Routes

**File: `app/main.py`**

- Import and register jobs router: `app.include_router(jobs_router.router, prefix="/api/v1/jobs", tags=["jobs"])`

### Step 11: Create Worker Startup Script

**New File: `worker.py`**

```python
#!/usr/bin/env python
from rq import Worker
from app.workers.queue import get_redis_connection, get_queue

if __name__ == '__main__':
    redis_conn = get_redis_connection()
    queues = [get_queue('scoring'), get_queue('default')]
    worker = Worker(queues, connection=redis_conn)
    worker.work()
```

### Step 12: Update Configuration

**File: `app/core/config.py`**

- Ensure `redis_url` is properly configured (already present)

**File: `env.example`**

- Add example: `REDIS_URL=redis://localhost:6379/0`

### Step 13: Documentation

**New File: `ASYNC_WORKFLOW.md`**

- Document the async flow
- API usage examples
- Worker deployment instructions

## API Usage Examples

### Client Flow:

```python
# 1. Upload CVs with persona selection
response = requests.post('/api/v1/candidate/upload-batch', 
    files=[('files', open('cv1.pdf', 'rb')), ('files', open('cv2.pdf', 'rb'))],
    data={'persona_id': 'persona-123'}
)
job_id = response.json()['job_id']

# 2. Poll for status
while True:
    status = requests.get(f'/api/v1/jobs/{job_id}/status').json()
    if status['status'] in ['completed', 'failed']:
        break
    time.sleep(2)

# 3. Get results
if status['status'] == 'completed':
    scores = status['result']['scores']
```

## Worker Deployment

### Development:

```bash
# Terminal 1: Start FastAPI
uvicorn app.main:app --reload

# Terminal 2: Start RQ Worker
python worker.py
```

### Production:

```bash
# Use supervisor or systemd to manage workers
rq worker scoring default --url redis://localhost:6379/0
```

## Testing Strategy

1. Unit tests for job repository
2. Integration tests for task execution
3. API tests for upload-batch endpoint
4. End-to-end test for complete flow