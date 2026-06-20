"""
Main entry point for HackerRank Orchestrate solution.

This module loads claim data and coordinates the evidence review system.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import load_claims, load_sample_claims, DataLoader


def main():
    """Main entry point."""
    # Resolve dataset directory (one level up from code/)
    code_dir = Path(__file__).parent
    dataset_dir = code_dir.parent / "dataset"
    
    print(f"Loading claims from {dataset_dir}")
    
    # Load claims
    try:
        claims = load_claims(str(dataset_dir))
        print(f"✓ Loaded {len(claims)} claims")
        
        # Print first claim as example
        if claims:
            claim = claims[0]
            print(f"\nExample claim:")
            print(f"  User ID: {claim.user_id}")
            print(f"  Claim Object: {claim.claim_object}")
            print(f"  Images: {claim.image_ids}")
            print(f"  User Claim: {claim.user_claim[:100]}...")
            
            if claim.user_history:
                print(f"  User History: {claim.user_history.past_claim_count} prior claims")
            
            if claim.evidence_requirements:
                print(f"  Evidence Rules: {len(claim.evidence_requirements)} requirements")
    
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
