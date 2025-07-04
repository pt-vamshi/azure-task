#!/usr/bin/env python3
"""
Deploy blob storage lifecycle management policy for cost optimization
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def deploy_lifecycle_policy():
    """Deploy the blob storage lifecycle management policy"""
    
    # Check if Azure CLI is installed
    try:
        subprocess.run(["az", "--version"], capture_output=True, check=True)
        print("✅ Azure CLI is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Azure CLI is not installed. Please install it first.")
        print("   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        return False
    
    # Check if logged in to Azure
    try:
        result = subprocess.run(["az", "account", "show"], capture_output=True, text=True, check=True)
        account_info = json.loads(result.stdout)
        print(f"✅ Logged in to Azure as: {account_info.get('user', {}).get('name', 'Unknown')}")
    except subprocess.CalledProcessError:
        print("❌ Not logged in to Azure. Please run 'az login' first.")
        return False
    
    # Get storage account name from environment
    connection_string = os.getenv("BLOB_CONNECTION_STRING")
    if not connection_string:
        print("❌ BLOB_CONNECTION_STRING environment variable not set")
        return False
    
    # Extract storage account name from connection string
    try:
        for part in connection_string.split(";"):
            if part.startswith("AccountName="):
                storage_account = part.split("=")[1]
                break
        else:
            print("❌ Could not extract storage account name from connection string")
            return False
    except Exception as e:
        print(f"❌ Error parsing connection string: {e}")
        return False
    
    print(f"📦 Storage Account: {storage_account}")
    
    # Load lifecycle policy
    policy_file = Path("blob_lifecycle_policy.json")
    if not policy_file.exists():
        print("❌ blob_lifecycle_policy.json not found")
        return False
    
    try:
        with open(policy_file, 'r') as f:
            policy = json.load(f)
        print("✅ Loaded lifecycle policy configuration")
    except Exception as e:
        print(f"❌ Error loading policy file: {e}")
        return False
    
    # Deploy the policy
    try:
        print("🚀 Deploying lifecycle management policy...")
        
        # Create temporary policy file with proper format
        temp_policy = {
            "rules": policy["rules"]
        }
        
        with open("temp_policy.json", 'w') as f:
            json.dump(temp_policy, f, indent=2)
        
        # Deploy using Azure CLI
        cmd = [
            "az", "storage", "account", "management-policy", "create",
            "--account-name", storage_account,
            "--policy", "temp_policy.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Lifecycle management policy deployed successfully")
        
        # Clean up temporary file
        Path("temp_policy.json").unlink(missing_ok=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to deploy policy: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error deploying policy: {e}")
        return False

def show_policy_info():
    """Show information about the lifecycle policy"""
    print("\n📋 Lifecycle Policy Configuration:")
    print("=" * 50)
    print("• Move blobs to Cool tier after 30 days")
    print("• Move blobs to Archive tier after 90 days")
    print("• Delete blobs after 7 years (2555 days)")
    print("• Applies to all blobs in 'billing-archive/' container")
    print("\n💰 Cost Benefits:")
    print("• Hot tier: ~$0.0184 per GB per month")
    print("• Cool tier: ~$0.01 per GB per month (46% savings)")
    print("• Archive tier: ~$0.00099 per GB per month (95% savings)")

def main():
    """Main function"""
    print("🔧 Blob Storage Lifecycle Policy Deployment")
    print("=" * 50)
    
    show_policy_info()
    
    response = input("\n🚀 Would you like to deploy the lifecycle policy? (y/n): ")
    if response.lower() in ['y', 'yes']:
        if deploy_lifecycle_policy():
            print("\n🎉 Lifecycle policy deployment completed!")
            print("\n📊 The policy will automatically:")
            print("   • Move archived billing records to Cool tier after 30 days")
            print("   • Move to Archive tier after 90 days")
            print("   • Delete after 7 years")
        else:
            print("\n❌ Lifecycle policy deployment failed")
            sys.exit(1)
    else:
        print("\n⏹️  Deployment cancelled")

if __name__ == "__main__":
    main() 