#!/usr/bin/env python3
"""
Deployment script for the billing archival system
This script helps set up and validate the system configuration
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "azure-cosmos",
        "azure-storage-blob", 
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ All dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def check_environment_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("📝 Creating .env file from template...")
        
        try:
            # Copy from env.example if it exists
            example_file = Path("env.example")
            if example_file.exists():
                with open(example_file, 'r') as f:
                    content = f.read()
                
                with open(env_file, 'w') as f:
                    f.write(content)
                
                print("✅ Created .env file from template")
                print("⚠️  Please edit .env file with your Azure credentials")
                return False
            else:
                print("❌ env.example file not found")
                return False
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    
    # Check required environment variables
    required_vars = [
        "COSMOS_ENDPOINT",
        "COSMOS_KEY", 
        "BLOB_CONNECTION_STRING"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("⚠️  Please set these variables in your .env file")
        return False
    
    print("✅ Environment variables configured")
    return True

def validate_azure_credentials():
    """Validate Azure credentials by testing connections"""
    print("\n🔐 Validating Azure Credentials...")
    
    try:
        from config import Config
        from cosmos_client import CosmosDBClient
        from blob_client import BlobStorageClient
        
        # Test Cosmos DB connection
        print("Testing Cosmos DB connection...")
        cosmos_client = CosmosDBClient()
        print("✅ Cosmos DB connection successful")
        
        # Test Blob Storage connection
        print("Testing Blob Storage connection...")
        blob_client = BlobStorageClient()
        print("✅ Blob Storage connection successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure credentials validation failed: {e}")
        return False

def create_sample_data():
    """Create sample billing records for testing"""
    print("\n📝 Creating Sample Data...")
    
    try:
        import requests
        from datetime import datetime, timedelta
        
        base_url = "http://localhost:8000"
        
        # Wait for API to be ready
        print("Waiting for API to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ API is ready")
                    break
            except:
                if i == 29:
                    print("❌ API is not responding")
                    return False
                import time
                time.sleep(1)
        
        # Create sample records
        sample_records = [
            {
                "customer_id": "customer-001",
                "amount": 299.99,
                "currency": "USD",
                "status": "paid",
                "description": "Monthly subscription",
                "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "due_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "paid_at": (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                "customer_id": "customer-002", 
                "amount": 599.99,
                "currency": "USD",
                "status": "pending",
                "description": "Annual subscription",
                "created_at": (datetime.utcnow() - timedelta(days=100)).isoformat(),
                "due_date": (datetime.utcnow() - timedelta(days=70)).isoformat()
            },
            {
                "customer_id": "customer-003",
                "amount": 199.99,
                "currency": "USD", 
                "status": "overdue",
                "description": "Quarterly subscription",
                "created_at": (datetime.utcnow() - timedelta(days=95)).isoformat(),
                "due_date": (datetime.utcnow() - timedelta(days=65)).isoformat()
            }
        ]
        
        for i, record in enumerate(sample_records, 1):
            try:
                response = requests.post(
                    f"{base_url}/billing",
                    json=record,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    print(f"✅ Created sample record {i}")
                else:
                    print(f"❌ Failed to create sample record {i}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error creating sample record {i}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def run_tests():
    """Run the test suite"""
    print("\n🧪 Running Tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_example.py"], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Tests completed successfully")
            return True
        else:
            print(f"❌ Tests failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Billing Archival System Deployment")
    print("=" * 50)
    
    # Step 1: Check Python version
    if not check_python_version():
        return False
    
    # Step 2: Check dependencies
    if not check_dependencies():
        return False
    
    # Step 3: Check environment configuration
    if not check_environment_file():
        print("\n⚠️  Please configure your .env file and run this script again")
        return False
    
    # Step 4: Validate Azure credentials
    if not validate_azure_credentials():
        print("\n⚠️  Please check your Azure credentials and run this script again")
        return False
    
    print("\n✅ System validation completed successfully!")
    
    # Ask user if they want to start the API
    response = input("\n🚀 Would you like to start the API server? (y/n): ")
    if response.lower() in ['y', 'yes']:
        print("\n🌐 Starting API server...")
        print("API will be available at: http://localhost:8000")
        print("API documentation at: http://localhost:8000/docs")
        print("Press Ctrl+C to stop the server")
        
        try:
            subprocess.run([sys.executable, "api.py"])
        except KeyboardInterrupt:
            print("\n⏹️  Server stopped")
    
    # Ask user if they want to create sample data
    response = input("\n📝 Would you like to create sample data? (y/n): ")
    if response.lower() in ['y', 'yes']:
        create_sample_data()
    
    # Ask user if they want to run tests
    response = input("\n🧪 Would you like to run tests? (y/n): ")
    if response.lower() in ['y', 'yes']:
        run_tests()
    
    print("\n🎉 Deployment completed!")
    print("\n📚 Next steps:")
    print("1. Start the API: python api.py")
    print("2. View API docs: http://localhost:8000/docs")
    print("3. Run tests: python test_example.py")
    print("4. Deploy Azure Function: See README.md for instructions")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Deployment interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1) 