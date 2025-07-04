#!/usr/bin/env python3
"""
Test example for the billing archival system
This file demonstrates how to test the various components of the system
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import BillingRecord, BillingStatus

class BillingArchivalTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def create_test_record(self, record_id: str, days_old: int = 100) -> Optional[Dict[str, Any]]:
        """Create a test billing record"""
        record_data = {
            "id": record_id,
            "customer_id": f"customer-{record_id}",
            "amount": 299.99,
            "currency": "USD",
            "status": "paid",
            "description": f"Test record {record_id}",
            "created_at": (datetime.utcnow() - timedelta(days=days_old)).isoformat(),
            "due_date": (datetime.utcnow() - timedelta(days=days_old-30)).isoformat(),
            "paid_at": (datetime.utcnow() - timedelta(days=days_old-15)).isoformat(),
            "metadata": {
                "test": True,
                "created_by": "test_script"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/billing",
                json=record_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Created test record: {record_id}")
                return response.json()
            else:
                print(f"❌ Failed to create test record {record_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error creating test record {record_id}: {str(e)}")
            return None
    
    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a billing record"""
        try:
            response = self.session.get(f"{self.base_url}/billing/{record_id}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Retrieved record {record_id} from {result.get('source', 'unknown')}")
                return result
            else:
                print(f"❌ Failed to retrieve record {record_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error retrieving record {record_id}: {str(e)}")
            return None
    
    def trigger_archival(self) -> Optional[Dict[str, Any]]:
        """Trigger the archival process"""
        try:
            response = self.session.post(f"{self.base_url}/archive/sync")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Archival completed: {result.get('message', 'Unknown')}")
                print(f"   Records archived: {result.get('archived_count', 0)}")
                return result
            else:
                print(f"❌ Archival failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error triggering archival: {str(e)}")
            return None
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get system statistics"""
        try:
            response = self.session.get(f"{self.base_url}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                print("📊 System Statistics:")
                print(f"   Cosmos DB records: {stats.get('cosmos_db_records', 0)}")
                print(f"   Archived records: {stats.get('archived_records', 0)}")
                print(f"   Blob storage files: {stats.get('blob_storage_files', 0)}")
                print(f"   Archival threshold: {stats.get('archival_threshold_days', 0)} days")
                return stats
            else:
                print(f"❌ Failed to get stats: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return None
    
    def restore_record(self, record_id: str) -> bool:
        """Restore a record from archive"""
        try:
            response = self.session.post(f"{self.base_url}/restore/{record_id}")
            
            if response.status_code == 200:
                print(f"✅ Restored record: {record_id}")
                return True
            else:
                print(f"❌ Failed to restore record {record_id}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error restoring record {record_id}: {str(e)}")
            return False
    
    def run_full_test(self):
        """Run a complete test of the archival system"""
        print("🚀 Starting Billing Archival System Test")
        print("=" * 50)
        
        # 1. Health check
        if not self.test_health_check():
            print("❌ Health check failed, stopping test")
            return
        
        # 2. Get initial stats
        print("\n📊 Initial Statistics:")
        initial_stats = self.get_stats()
        
        # 3. Create test records
        print("\n📝 Creating Test Records:")
        test_records = []
        
        # Create recent record (should stay in Cosmos DB)
        recent_record = self.create_test_record("test-recent-001", days_old=30)
        if recent_record:
            test_records.append("test-recent-001")
        
        # Create old record (should be archived)
        old_record = self.create_test_record("test-old-001", days_old=100)
        if old_record:
            test_records.append("test-old-001")
        
        # Create another old record
        old_record2 = self.create_test_record("test-old-002", days_old=95)
        if old_record2:
            test_records.append("test-old-002")
        
        # 4. Verify records exist in Cosmos DB
        print("\n🔍 Verifying Records in Cosmos DB:")
        for record_id in test_records:
            self.get_record(record_id)
        
        # 5. Get stats after creation
        print("\n📊 Statistics After Record Creation:")
        self.get_stats()
        
        # 6. Trigger archival
        print("\n🔄 Triggering Archival Process:")
        archival_result = self.trigger_archival()
        
        # 7. Get stats after archival
        print("\n📊 Statistics After Archival:")
        self.get_stats()
        
        # 8. Verify records are still accessible
        print("\n🔍 Verifying Records After Archival:")
        for record_id in test_records:
            self.get_record(record_id)
        
        # 9. Test restoration
        print("\n🔄 Testing Record Restoration:")
        if test_records:
            self.restore_record(test_records[0])
            
            # Verify restoration
            print("\n🔍 Verifying Restored Record:")
            self.get_record(test_records[0])
        
        # 10. Final stats
        print("\n📊 Final Statistics:")
        self.get_stats()
        
        print("\n✅ Test completed!")

def main():
    """Main test function"""
    # Check if API is running
    tester = BillingArchivalTester()
    
    try:
        tester.run_full_test()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    main() 