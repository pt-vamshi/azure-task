from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
from typing import Optional, Dict, Any
import json
import logging
from config import Config
from models import ArchiveIndex

logger = logging.getLogger(__name__)

class BlobStorageClient:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(Config.BLOB_CONNECTION_STRING)
        self.container_client = self.blob_service_client.get_container_client(Config.BLOB_CONTAINER)
        
        # Ensure container exists
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Ensure the blob container exists"""
        try:
            self.container_client.get_container_properties()
        except ResourceNotFoundError:
            logger.info(f"Creating blob container: {Config.BLOB_CONTAINER}")
            self.container_client.create_container()
    
    def upload_billing_record(self, record_id: str, record_data: Dict[str, Any]) -> str:
        """Upload a billing record to blob storage with Cool tier for cost optimization"""
        try:
            blob_name = f"{record_id}.json"
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Convert record data to JSON string
            json_data = json.dumps(record_data, default=str)
            
            # Upload the blob with Cool tier for cost optimization
            blob_client.upload_blob(
                json_data, 
                overwrite=True,
                standard_blob_tier="Cool"  # Use Cool tier for archived data
            )
            
            logger.info(f"Uploaded billing record to blob storage (Cool tier): {blob_name}")
            return blob_name
        except Exception as e:
            logger.error(f"Error uploading billing record {record_id} to blob storage: {str(e)}")
            raise
    
    def download_billing_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Download a billing record from blob storage"""
        try:
            blob_name = f"{record_id}.json"
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Download the blob content
            blob_data = blob_client.download_blob()
            content = blob_data.readall()
            
            # Parse JSON content
            record_data = json.loads(content.decode('utf-8'))
            
            logger.info(f"Downloaded billing record from blob storage: {blob_name}")
            return record_data
        except ResourceNotFoundError:
            logger.warning(f"Billing record not found in blob storage: {record_id}")
            return None
        except Exception as e:
            logger.error(f"Error downloading billing record {record_id} from blob storage: {str(e)}")
            raise
    
    def download_billing_record_by_path(self, blob_path: str) -> Optional[Dict[str, Any]]:
        """Download a billing record from blob storage using a specific path"""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            
            # Download the blob content
            blob_data = blob_client.download_blob()
            content = blob_data.readall()
            
            # Parse JSON content
            record_data = json.loads(content.decode('utf-8'))
            
            logger.info(f"Downloaded billing record from blob storage: {blob_path}")
            return record_data
        except ResourceNotFoundError:
            logger.warning(f"Billing record not found in blob storage: {blob_path}")
            return None
        except Exception as e:
            logger.error(f"Error downloading billing record from blob storage: {blob_path}, error: {str(e)}")
            raise
    
    def delete_billing_record(self, record_id: str) -> bool:
        """Delete a billing record from blob storage"""
        try:
            blob_name = f"{record_id}.json"
            blob_client = self.container_client.get_blob_client(blob_name)
            
            blob_client.delete_blob()
            logger.info(f"Deleted billing record from blob storage: {blob_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Record not found in blob storage for deletion: {record_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting billing record {record_id} from blob storage: {str(e)}")
            raise
    
    def blob_exists(self, record_id: str) -> bool:
        """Check if a billing record exists in blob storage"""
        try:
            blob_name = f"{record_id}.json"
            blob_client = self.container_client.get_blob_client(blob_name)
            
            return blob_client.exists()
        except Exception as e:
            logger.error(f"Error checking if blob exists {record_id}: {str(e)}")
            return False
    
    def list_archived_records(self, prefix: Optional[str] = None) -> list:
        """List all archived billing records"""
        try:
            blobs = []
            for blob in self.container_client.list_blobs(name_starts_with=prefix):
                blobs.append(blob.name)
            
            logger.info(f"Found {len(blobs)} archived records")
            return blobs
        except Exception as e:
            logger.error(f"Error listing archived records: {str(e)}")
            raise 