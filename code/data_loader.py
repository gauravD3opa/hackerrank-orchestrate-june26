"""
Data loading layer for HackerRank Orchestrate.

Reads and joins all four CSVs (claims, user_history, evidence_requirements, images)
into in-memory ClaimRecord objects for processing.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pandas as pd


@dataclass
class UserHistoryRecord:
    """User history information for risk context."""
    user_id: str
    past_claim_count: int
    accept_claim: int
    manual_review_claim: int
    rejected_claim: int
    last_90_days_claim_count: int
    history_flags: str
    history_summary: str


@dataclass
class EvidenceRequirementRecord:
    """Evidence requirement rule for a specific claim object type and issue family."""
    requirement_id: str
    claim_object: str  # 'car', 'laptop', 'package', or 'all'
    applies_to: str
    minimum_image_evidence: str


@dataclass
class ClaimRecord:
    """
    Complete record for a single claim, with all supporting data joined together.
    
    Attributes:
        user_id: User ID from claims.csv
        image_paths: Semicolon-separated image paths as string
        image_path_list: Parsed list of individual image paths
        image_ids: Extracted image IDs (filenames without extension)
        user_claim: Claim conversation/transcript
        claim_object: 'car', 'laptop', or 'package'
        user_history: User's history record (may be None if not found)
        evidence_requirements: List of applicable evidence requirement rules
    """
    user_id: str
    image_paths: str
    image_path_list: List[str] = field(default_factory=list)
    image_ids: List[str] = field(default_factory=list)
    user_claim: str = ""
    claim_object: str = ""
    user_history: Optional[UserHistoryRecord] = None
    evidence_requirements: List[EvidenceRequirementRecord] = field(default_factory=list)
    
    def __post_init__(self):
        """Parse image paths and extract image IDs."""
        if self.image_paths:
            self.image_path_list = [p.strip() for p in self.image_paths.split(";")]
            # Extract image IDs: filename without extension
            self.image_ids = [Path(p).stem for p in self.image_path_list]


class DataLoader:
    """Loads and joins all required data into ClaimRecord objects."""
    
    def __init__(self, dataset_dir: str):
        """
        Initialize the data loader.
        
        Args:
            dataset_dir: Path to the dataset directory containing CSVs and images
        """
        self.dataset_dir = Path(dataset_dir)
        self.claims_df: Optional[pd.DataFrame] = None
        self.user_history_df: Optional[pd.DataFrame] = None
        self.evidence_requirements_df: Optional[pd.DataFrame] = None
        
        # Lookup dictionaries
        self.user_history_lookup: Dict[str, UserHistoryRecord] = {}
        self.evidence_requirements_by_object: Dict[str, List[EvidenceRequirementRecord]] = {}
    
    def load_all(self, claims_file: str = "claims.csv") -> List[ClaimRecord]:
        """
        Load all data and return a list of ClaimRecord objects.
        
        Args:
            claims_file: Name of the claims CSV file to load (default: claims.csv)
        
        Returns:
            List of ClaimRecord objects with all data joined together
        """
        self._load_csvs(claims_file)
        self._build_lookups()
        return self._join_and_create_records()
    
    def _load_csvs(self, claims_file: str):
        """Load all CSV files."""
        claims_path = self.dataset_dir / claims_file
        user_history_path = self.dataset_dir / "user_history.csv"
        evidence_requirements_path = self.dataset_dir / "evidence_requirements.csv"
        
        # Load with string dtypes to preserve any formatting
        self.claims_df = pd.read_csv(claims_path, dtype=str)
        self.user_history_df = pd.read_csv(user_history_path, dtype=str)
        self.evidence_requirements_df = pd.read_csv(evidence_requirements_path, dtype=str)
        
        # Validate required columns
        required_claims_cols = {"user_id", "image_paths", "user_claim", "claim_object"}
        if not required_claims_cols.issubset(self.claims_df.columns):
            raise ValueError(f"Claims CSV missing required columns. Expected: {required_claims_cols}")
        
        required_user_cols = {"user_id"}
        if not required_user_cols.issubset(self.user_history_df.columns):
            raise ValueError("User history CSV missing required columns")
        
        required_evidence_cols = {"claim_object", "minimum_image_evidence"}
        if not required_evidence_cols.issubset(self.evidence_requirements_df.columns):
            raise ValueError("Evidence requirements CSV missing required columns")
    
    def _build_lookups(self):
        """Build lookup dictionaries for user history and evidence requirements."""
        # Build user history lookup
        for _, row in self.user_history_df.iterrows():
            user_id = row["user_id"]
            record = UserHistoryRecord(
                user_id=user_id,
                past_claim_count=int(row.get("past_claim_count", 0) or 0),
                accept_claim=int(row.get("accept_claim", 0) or 0),
                manual_review_claim=int(row.get("manual_review_claim", 0) or 0),
                rejected_claim=int(row.get("rejected_claim", 0) or 0),
                last_90_days_claim_count=int(row.get("last_90_days_claim_count", 0) or 0),
                history_flags=str(row.get("history_flags", "none")),
                history_summary=str(row.get("history_summary", "")),
            )
            self.user_history_lookup[user_id] = record
        
        # Build evidence requirements lookup by claim_object
        # Include both specific and 'all' rules
        for _, row in self.evidence_requirements_df.iterrows():
            claim_object = row["claim_object"]
            record = EvidenceRequirementRecord(
                requirement_id=row.get("requirement_id", ""),
                claim_object=claim_object,
                applies_to=row.get("applies_to", ""),
                minimum_image_evidence=row.get("minimum_image_evidence", ""),
            )
            
            # Store under specific object and 'all'
            for obj in (claim_object, "all") if claim_object != "all" else ("all",):
                if obj not in self.evidence_requirements_by_object:
                    self.evidence_requirements_by_object[obj] = []
                if record not in self.evidence_requirements_by_object[obj]:
                    self.evidence_requirements_by_object[obj].append(record)
    
    def _join_and_create_records(self) -> List[ClaimRecord]:
        """Create ClaimRecord objects by joining all data."""
        records = []
        
        for _, row in self.claims_df.iterrows():
            user_id = row["user_id"]
            claim_object = row["claim_object"]
            
            # Look up user history
            user_history = self.user_history_lookup.get(user_id)
            
            # Look up evidence requirements (both specific object type and 'all')
            evidence_reqs = []
            if claim_object in self.evidence_requirements_by_object:
                evidence_reqs.extend(self.evidence_requirements_by_object[claim_object])
            # Don't duplicate 'all' rules if already included
            if claim_object != "all" and "all" in self.evidence_requirements_by_object:
                for req in self.evidence_requirements_by_object["all"]:
                    if req not in evidence_reqs:
                        evidence_reqs.append(req)
            
            # Create claim record
            record = ClaimRecord(
                user_id=user_id,
                image_paths=row["image_paths"],
                user_claim=row["user_claim"],
                claim_object=claim_object,
                user_history=user_history,
                evidence_requirements=evidence_reqs,
            )
            records.append(record)
        
        return records
    
    def get_image_path(self, relative_image_path: str) -> Path:
        """
        Resolve a relative image path to an absolute path.
        
        Args:
            relative_image_path: Path like "images/test/case_001/img_1.jpg"
        
        Returns:
            Absolute Path to the image file
        """
        return self.dataset_dir / relative_image_path
    
    def image_exists(self, relative_image_path: str) -> bool:
        """Check if an image file exists."""
        return self.get_image_path(relative_image_path).exists()


def load_claims(dataset_dir: str, claims_file: str = "claims.csv") -> List[ClaimRecord]:
    """
    Convenience function to load claims data.
    
    Args:
        dataset_dir: Path to the dataset directory
        claims_file: Name of the claims CSV file (default: claims.csv)
    
    Returns:
        List of ClaimRecord objects with all data joined
    """
    loader = DataLoader(dataset_dir)
    return loader.load_all(claims_file)


def load_sample_claims(dataset_dir: str) -> List[ClaimRecord]:
    """Load sample claims for evaluation."""
    loader = DataLoader(dataset_dir)
    return loader.load_all("sample_claims.csv")
