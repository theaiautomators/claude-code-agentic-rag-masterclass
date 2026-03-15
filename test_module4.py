"""Smoke test for Module 4: Record Manager"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

from server.main import ingest_file, list_documents
from supabase import create_client

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

TEST_FILE = 'test_data/sample.txt'

print('=== Setup: Clean up any existing sample.txt document ===')
existing = client.table('documents').select('id').eq('filename', 'sample.txt').execute()
for doc in existing.data:
    client.table('documents').delete().eq('id', doc['id']).execute()
    print(f'  Deleted existing doc: {doc["id"]}')

print()
print('=== Step 1: First ingest ===')
r1 = ingest_file(TEST_FILE)
print(r1)
assert r1['status'] == 'completed', f"Expected completed, got {r1}"

print()
print('=== Step 2: Ingest same file again (expect skipped) ===')
r2 = ingest_file(TEST_FILE)
print(r2)
assert r2['status'] == 'skipped', f"Expected skipped, got {r2}"
assert r2['reason'] == 'duplicate'

print()
print('=== Step 3: Modify content and re-ingest (expect new doc) ===')
original = open(TEST_FILE).read()
modified = original + '\n\n## New Section\nAdded to test re-ingestion on content change.'
with open(TEST_FILE, 'w') as f:
    f.write(modified)

old_id = r1['document_id']
r3 = ingest_file(TEST_FILE)
print(r3)
assert r3['status'] == 'completed', f"Expected completed, got {r3}"
assert r3['document_id'] != old_id, "Expected a new document id after content change"

print()
print('=== Step 4: Verify no orphan chunks ===')
old_chunks = client.table('chunks').select('id').eq('document_id', old_id).execute()
new_chunks = client.table('chunks').select('id').eq('document_id', r3['document_id']).execute()
print(f'Old doc orphan chunks (should be 0): {len(old_chunks.data)}')
print(f'New doc chunks: {len(new_chunks.data)}')
assert len(old_chunks.data) == 0, "Orphan chunks found for deleted document!"
assert len(new_chunks.data) > 0, "No chunks found for new document!"

print()
print('=== Step 5: Restore original file ===')
with open(TEST_FILE, 'w') as f:
    f.write(original)

print()
print('All assertions passed. Module 4 smoke test COMPLETE.')
