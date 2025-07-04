import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Cosmos DB Configuration
    COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
    COSMOS_KEY = os.getenv("COSMOS_KEY")
    COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "billingdb")
    COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "records")
    COSMOS_ARCHIVE_INDEX_CONTAINER = os.getenv("COSMOS_ARCHIVE_INDEX_CONTAINER", "archive_index")
    
    # Azure Blob Storage Configuration
    BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
    BLOB_CONTAINER = os.getenv("BLOB_CONTAINER", "billing-archive")
    
    # Archival Configuration
    ARCHIVAL_DAYS_THRESHOLD = int(os.getenv("ARCHIVAL_DAYS_THRESHOLD", "90"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            "COSMOS_ENDPOINT",
            "COSMOS_KEY", 
            "BLOB_CONNECTION_STRING"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True 