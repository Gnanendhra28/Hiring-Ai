# AI Hiring & Adaptive Multi-Turn Interview Platform

An enterprise multi-tenant AI recruitment intelligence and live adaptive candidate interview platform powered by Google Gemini, Firebase Authentication, Cloud Firestore, Google Cloud SQL (PostgreSQL + pgvector), Google Cloud Secret Manager, and Google Cloud Run.

---

## 1. System Architecture

```
                                  [ Candidate / Recruiter ]
                                              │
                                              ▼
                                 [ Next.js 14 Web Frontend ]
                                  (Firebase Auth Client SDK)
                                              │
                                   Authorization: Bearer <ID_TOKEN>
                                              │
                                              ▼
                                 [ Google Cloud Run Service ]
                                     (ai-interview-api)
                                 (FastAPI Backend / asia-south1)
                                              │
         ┌───────────────────────────┬────────┴──────────────────────────┐
         ▼                           ▼                                   ▼
[ Google Cloud Secret Manager ] [ Google Cloud Firestore ]   [ Google Cloud SQL (PostgreSQL) ]
 - GEMINI_API_KEY                (hiring-ai-4ae76)            (hiring-ai-507307:asia-south1:hiring-ai-pg)
 - SECRET_KEY                    - /interviews/{id}           - Canonical Requisitions & Jobs
 - DATABASE_URL                  - /interviews/{id}/turns     - Candidate Skills & Resumes
                                 - /interviews/{id}/scorecard - pgvector HNSW Semantic Match
         │
         ▼
 [ Google Gemini Engine ]
 - Model Ladder: gemini-3.6-flash -> gemini-3.1-flash-lite -> gemini-flash-latest -> gemini-3.7-flash
 - Adaptive Real-Time Probing & Gap Detection
 - LLM-as-a-Judge Multi-Dimensional Evaluation Scorecard
```

---

## 2. Target Environment & Cloud Resources

| Component | Resource ID / Region | Status |
| :--- | :--- | :---: |
| **Google Cloud Deployment Project** | `hiring-ai-507307` | ACTIVE |
| **Firebase & Firestore Project** | `hiring-ai-4ae76` | ACTIVE |
| **Cloud Run Region** | `asia-south1` | ACTIVE |
| **Backend Cloud Run Service** | `ai-interview-api` | LIVE (`ai-interview-api-00012-tl4`) |
| **Backend Service URL** | `https://ai-interview-api-30597175496.asia-south1.run.app` | READY |
| **Frontend Cloud Run Service** | `ai-interview-frontend` | LIVE (`ai-interview-frontend-00001-xrn`) |
| **Frontend Service URL** | `https://ai-interview-frontend-30597175496.asia-south1.run.app` | READY |
| **Cloud SQL PostgreSQL Instance** | `hiring-ai-pg` (`asia-south1`) | RUNNABLE |
| **Required Verification Label** | `dev-tutorial=cloud-run-ai-challenge` | VERIFIED |

---

## 3. Required Google Cloud APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  datastore.googleapis.com \
  --project=hiring-ai-507307
```

---

## 4. Secret Manager Configuration

Create production secrets securely in Google Cloud Secret Manager:

```bash
# 1. Create Secrets
gcloud secrets create GEMINI_API_KEY --replication-policy="automatic" --project=hiring-ai-507307
gcloud secrets create SECRET_KEY --replication-policy="automatic" --project=hiring-ai-507307
gcloud secrets create DATABASE_URL --replication-policy="automatic" --project=hiring-ai-507307

# 2. Add Secret Versions
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add GEMINI_API_KEY --data-file=- --project=hiring-ai-507307
echo -n "YOUR_JWT_SECRET" | gcloud secrets versions add SECRET_KEY --data-file=- --project=hiring-ai-507307
echo -n "postgresql+asyncpg://app_user:SECURE_DB_PASSWORD@/hiring_db?host=/cloudsql/hiring-ai-507307:asia-south1:hiring-ai-pg" | \
  gcloud secrets versions add DATABASE_URL --data-file=- --project=hiring-ai-507307
```

---

## 5. IAM & Least-Privilege Role Bindings

```bash
# Grant Secret Manager Access on Deployment Host Project
gcloud projects add-iam-policy-binding hiring-ai-507307 \
  --member="serviceAccount:30597175496-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Grant Cloud SQL Client Access
gcloud projects add-iam-policy-binding hiring-ai-507307 \
  --member="serviceAccount:30597175496-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Grant Firestore Access on Firebase Project
gcloud projects add-iam-policy-binding hiring-ai-4ae76 \
  --member="serviceAccount:30597175496-compute@developer.gserviceaccount.com" \
  --role="roles/datastore.user"
```

---

## 6. Cloud Run Build & Deployment

```bash
# Submit automated Cloud Build pipeline
gcloud builds submit --config=cloudbuild.yaml --project=hiring-ai-507307
```

---

## 7. Firestore Security Rules

Deploy production `firestore.rules`:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isAuthenticated() {
      return request.auth != null && request.auth.uid != null;
    }
    function isOwner(userId) {
      return isAuthenticated() && request.auth.uid == userId;
    }
    function isRecruiterOrAdmin() {
      return isAuthenticated() && (
        request.auth.token.role == 'RECRUITER' ||
        request.auth.token.role == 'ORGANIZATION_ADMIN' ||
        request.auth.token.role == 'PLATFORM_ADMIN'
      );
    }

    match /users/{userId} {
      allow read: if isAuthenticated() && (isOwner(userId) || isRecruiterOrAdmin());
      allow create: if isAuthenticated() && isOwner(userId) && !request.resource.data.keys().hasAny(['role', 'is_admin', 'is_platform_admin']);
      allow update: if isAuthenticated() && isOwner(userId) && !request.resource.data.diff(resource.data).affectedKeys().hasAny(['role', 'is_admin', 'is_platform_admin']);
      allow delete: if false;
    }

    match /interviews/{interviewId} {
      allow read: if isAuthenticated() && (
        resource.data.candidate_id == request.auth.uid ||
        isRecruiterOrAdmin()
      );
      allow create, update: if isAuthenticated() && isRecruiterOrAdmin();
      allow delete: if false;

      match /turns/{turnId} {
        allow read, create: if isAuthenticated();
        allow update, delete: if false;
      }

      match /scorecard/{scorecardId} {
        allow read: if isAuthenticated();
        allow write: if isRecruiterOrAdmin();
      }
    }

    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

---

## 8. Automated Test Execution

```bash
# Run backend test suite (216 tests)
pytest backend/tests/ candidate_ingestion_pipeline/test_pipeline.py ai_matching_engine/tests/test_matching_engine.py

# Run frontend build verification (41 routes)
cd frontend && npm run build
```
