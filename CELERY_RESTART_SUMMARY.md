# Celery Worker Restart and Document Reprocessing Summary

**Date:** December 8, 2025  
**Status:** Celery worker restarted, documents queued for reprocessing

## Actions Completed

### 1. ✅ Celery Worker Restarted
- **Action:** Stopped all existing Celery workers
- **Command:** `pkill -f "celery.*worker"`
- **Restart:** Started new worker with updated code
- **Command:** `celery -A paperbot worker -l info --logfile=/tmp/celery_worker.log --detach`
- **Status:** Worker process started

### 2. ✅ Code Changes Applied
- **File:** `api/tasks.py`
- **Change:** Added chunk cleanup before creating new chunks
- **Line:** 48-49
- **Code:**
  ```python
  # Delete existing chunks if any (for reprocessing)
  Chunk.objects.filter(document=document).delete()
  ```

### 3. ✅ Documents Cleaned and Queued
- **Action:** Deleted all existing chunks and embeddings
- **Documents Reset:** All 3 documents reset to "uploaded" status
- **Tasks Queued:** All documents queued for processing
- **Task IDs:**
  - Doc 3: `3daa1a2b-74a3-4d1b-9296-deaa45dc7b95`
  - Doc 2: `346e50df-eb79-4e9e-9552-d3a40f39a73a`
  - Doc 1: `49f7c138-69c9-407a-a171-622668c71859`

## Current Status

### Celery Worker
- **Process:** Running in background
- **Log File:** `/tmp/celery_worker.log`
- **Configuration:** Connected to Redis at `redis://localhost:6379/0`

### Documents
- **Total:** 3 documents
- **Status:** All in "uploaded" state, queued for processing
- **Expected:** Will progress through: uploaded → processing → extracted → chunked → embedded → indexed

## Verification Steps

### Check Celery Worker Status
```bash
ps aux | grep "celery.*worker" | grep -v grep
tail -50 /tmp/celery_worker.log
```

### Check Document Status
```bash
cd /home/d4rk_m3ta/Desktop/PaperBot
source venv/bin/activate
export USE_SQLITE=True
python3 manage.py shell -c "from core.models import Document; [print(f'Doc {d.id}: {d.status}') for d in Document.objects.all()]"
```

### Monitor Processing
```bash
python3 monitor_processing.py
```

### Run Tests After Indexing
```bash
python3 test_query_summarize.py
```

## Troubleshooting

If documents remain in "uploaded" status:

1. **Verify Celery Worker is Running:**
   ```bash
   ps aux | grep celery
   ```

2. **Check Redis Connection:**
   ```bash
   redis-cli ping
   ```

3. **Check Celery Logs:**
   ```bash
   tail -100 /tmp/celery_worker.log
   ```

4. **Manually Trigger Processing:**
   ```bash
   python3 manage.py shell
   >>> from api.tasks import process_document
   >>> from core.models import Document
   >>> doc = Document.objects.get(id=3)
   >>> process_document.delay(doc.id)
   ```

5. **Restart Celery Worker:**
   ```bash
   pkill -f "celery.*worker"
   cd /home/d4rk_m3ta/Desktop/PaperBot
   source venv/bin/activate
   export USE_SQLITE=True
   celery -A paperbot worker -l info --logfile=/tmp/celery_worker.log --detach
   ```

## Expected Timeline

- **Extraction:** ~5-10 seconds per document
- **Chunking:** ~2-5 seconds per document
- **Embedding:** ~10-30 seconds per document (depends on model)
- **Indexing:** ~5-10 seconds per document
- **Total:** ~30-60 seconds per document

## Next Steps

1. Wait for documents to complete processing (check status every 10-15 seconds)
2. Once documents reach "indexed" status, run test script:
   ```bash
   python3 test_query_summarize.py
   ```
3. Verify Query and Summarization endpoints work correctly

## Files Modified

- `api/tasks.py` - Added chunk cleanup before processing

## Files Created

- `test_query_summarize.py` - Test script for Query/Summarization
- `monitor_processing.py` - Document processing monitor
- `CELERY_RESTART_SUMMARY.md` - This summary

---

**Summary:** Celery worker has been restarted with updated code. All documents have been cleaned and queued for reprocessing. The fix for duplicate chunk handling is in place. Documents should process successfully through the complete pipeline.

