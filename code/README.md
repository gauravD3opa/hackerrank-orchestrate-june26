# Data Loading Layer

## Overview

The data loading layer (`data_loader.py`) provides a clean, type-safe interface for reading and joining all required CSV files and image data into in-memory `ClaimRecord` objects.

## Components

### `UserHistoryRecord`
Represents a user's claim history and risk profile.

```python
record = UserHistoryRecord(
    user_id="user_002",
    past_claim_count=4,
    accept_claim=3,
    manual_review_claim=1,
    rejected_claim=0,
    last_90_days_claim_count=2,
    history_flags="none",
    history_summary="Mostly accepted vehicle claims with one manual review"
)
```

### `EvidenceRequirementRecord`
Represents a single evidence requirement rule for a claim type and issue family.

```python
requirement = EvidenceRequirementRecord(
    requirement_id="REQ_CAR_BODY_PANEL",
    claim_object="car",
    applies_to="dent or scratch",
    minimum_image_evidence="The claimed car panel or bumper should be visible from an angle where surface marks or deformation can be assessed."
)
```

### `ClaimRecord`
The primary data structure combining all data for a single claim.

**Attributes:**
- `user_id`: User ID from claims.csv
- `image_paths`: Semicolon-separated image paths (string)
- `image_path_list`: Parsed list of individual image paths
- `image_ids`: Extracted image IDs (filenames without extension)
- `user_claim`: Claim conversation/transcript
- `claim_object`: One of: `car`, `laptop`, `package`
- `user_history`: UserHistoryRecord (may be None if user not found)
- `evidence_requirements`: List of applicable EvidenceRequirementRecord objects

**Example:**
```python
claim = claims[0]
print(claim.user_id)           # "user_002"
print(claim.claim_object)      # "car"
print(claim.image_ids)         # ['img_1', 'img_2', 'img_3']
print(claim.user_claim)        # Full conversation text
print(claim.user_history)      # UserHistoryRecord object or None
print(claim.evidence_requirements)  # List of EvidenceRequirementRecord
```

### `DataLoader`
Main class for loading and joining all data.

**Usage:**
```python
from data_loader import DataLoader

loader = DataLoader("../dataset")

# Load main claims
claims = loader.load_all("claims.csv")

# Or load sample claims for evaluation
sample_claims = loader.load_all("sample_claims.csv")

# Access individual records
for claim in claims:
    print(f"{claim.user_id}: {claim.claim_object}")
    
    # Get absolute image path
    img_path = loader.get_image_path(claim.image_path_list[0])
    
    # Check if image exists
    if loader.image_exists(claim.image_path_list[0]):
        # Process image...
        pass
```

## Convenience Functions

### `load_claims(dataset_dir, claims_file="claims.csv")`
Quick function to load claims data without instantiating DataLoader.

```python
from data_loader import load_claims

claims = load_claims("../dataset")
print(f"Loaded {len(claims)} claims")
```

### `load_sample_claims(dataset_dir)`
Load sample claims for evaluation.

```python
from data_loader import load_sample_claims

sample = load_sample_claims("../dataset")
print(f"Loaded {len(sample)} sample claims")
```

## Data Joining Logic

The `DataLoader` performs these joins:

1. **User History Join**: For each claim, looks up the user in `user_history.csv` by `user_id`. If not found, `claim.user_history` is `None`.

2. **Evidence Requirements Join**: For each claim, collects evidence requirement rules that apply to:
   - The specific `claim_object` (e.g., `"car"`)
   - The generic `"all"` rules (apply to all object types)

3. **Image ID Extraction**: Parses `image_paths` (semicolon-separated) and extracts image IDs from filenames. For example:
   - Path: `images/test/case_001/img_1.jpg` → ID: `img_1`
   - Path: `images/sample/case_003/damage_photo.jpg` → ID: `damage_photo`

## Error Handling

The loader validates CSV structure on load and raises `ValueError` if required columns are missing:

```python
try:
    claims = load_claims("../dataset")
except FileNotFoundError as e:
    print(f"Dataset directory not found: {e}")
except ValueError as e:
    print(f"CSV format error: {e}")
```

## CSV Column Requirements

### claims.csv
- `user_id`
- `image_paths` (semicolon-separated)
- `user_claim`
- `claim_object`

### user_history.csv
- `user_id` (required; other columns must exist)

### evidence_requirements.csv
- `claim_object`
- `minimum_image_evidence`
- (optional: `requirement_id`, `applies_to`)

## Performance Notes

- Entire dataset is loaded into memory. For large datasets (>10K claims), consider pagination or streaming.
- CSV parsing uses `dtype=str` to preserve all original data types (e.g., never convert numeric IDs to integers unless explicitly needed).
- Lookup dictionaries (user history, evidence requirements) are built once per `load_all()` call.

## Running the Example

```bash
cd code/
python main.py
```

Expected output:
```
Loading claims from C:\Users\gaura\source\repos\hackerrank-orchestrate-june26\dataset
✓ Loaded 44 claims

Example claim:
  User ID: user_002
  Claim Object: car
  Images: ['img_1', 'img_2', 'img_3']
  User Claim: Customer: Morning. I parked near office...
  User History: 4 prior claims
  Evidence Rules: 11 requirements
```
