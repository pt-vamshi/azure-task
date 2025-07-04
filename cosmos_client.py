from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from typing import List, Optional, Dict, Any
import logging
from config import Config
from models import BillingRecord, ArchiveIndex

logger = logging.getLogger(__name__)

class CosmosDBClient:
    def __init__(self):
        self.client = CosmosClient(Config.COSMOS_ENDPOINT, Config.COSMOS_KEY)
        self.database = self.client.get_database_client(Config.COSMOS_DATABASE)
        self.container = self.database.get_container_client(Config.COSMOS_CONTAINER)
        self.archive_index_container = self.database.get_container_client(Config.COSMOS_ARCHIVE_INDEX_CONTAINER)
        
        # Ensure containers exist
        self._ensure_containers_exist()
    
    def _ensure_containers_exist(self):
        """Ensure required containers exist in the database"""
        try:
            # Check if main container exists
            self.container.read()
        except CosmosResourceNotFoundError:
            logger.info(f"Creating container: {Config.COSMOS_CONTAINER}")
            self.database.create_container(
                id=Config.COSMOS_CONTAINER,
                partition_key=PartitionKey(path="/id")
            )
        
        try:
            # Check if archive index container exists
            self.archive_index_container.read()
        except CosmosResourceNotFoundError:
            logger.info(f"Creating container: {Config.COSMOS_ARCHIVE_INDEX_CONTAINER}")
            self.database.create_container(
                id=Config.COSMOS_ARCHIVE_INDEX_CONTAINER,
                partition_key=PartitionKey(path="/id")
            )
    
    def get_billing_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a billing record by ID"""
        try:
            response = self.container.read_item(item=record_id, partition_key=record_id)
            return response
        except CosmosResourceNotFoundError:
            logger.warning(f"Billing record not found in Cosmos DB: {record_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving billing record {record_id}: {str(e)}")
            raise
    
    def get_records_to_archive(self, cutoff_date: str) -> List[Dict[str, Any]]:
        """Get records older than the cutoff date for archival"""
        try:
            query = "SELECT * FROM c WHERE c.created_at < @cutoff"
            parameters = [{"name": "@cutoff", "value": cutoff_date}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Found {len(items)} records to archive")
            return items
        except Exception as e:
            logger.error(f"Error querying records for archival: {str(e)}")
            raise
    
    def delete_record(self, record_id: str) -> bool:
        """Delete a billing record from Cosmos DB"""
        try:
            self.container.delete_item(item=record_id, partition_key=record_id)
            logger.info(f"Deleted billing record: {record_id}")
            return True
        except CosmosResourceNotFoundError:
            logger.warning(f"Record not found for deletion: {record_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting billing record {record_id}: {str(e)}")
            raise
    
    def create_archive_index(self, archive_index: ArchiveIndex) -> bool:
        """Create an archive index entry"""
        try:
            self.archive_index_container.create_item(archive_index.dict())
            logger.info(f"Created archive index for record: {archive_index.id}")
            return True
        except Exception as e:
            logger.error(f"Error creating archive index for {archive_index.id}: {str(e)}")
            raise
    
    def get_archive_index(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get archive index entry for a record"""
        try:
            response = self.archive_index_container.read_item(
                item=record_id, 
                partition_key=record_id
            )
            return response
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error retrieving archive index for {record_id}: {str(e)}")
            raise
    
    def create_billing_record(self, record: BillingRecord) -> bool:
        """Create a new billing record"""
        try:
            self.container.create_item(record.dict())
            logger.info(f"Created billing record: {record.id}")
            return True
        except Exception as e:
            logger.error(f"Error creating billing record {record.id}: {str(e)}")
            raise
    
    def update_billing_record(self, record_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing billing record"""
        try:
            # First get the existing record
            existing_record = self.get_billing_record(record_id)
            if not existing_record:
                return False
            
            # Update with new values
            existing_record.update(updates)
            
            # Replace the record
            self.container.replace_item(
                item=record_id,
                body=existing_record,
                partition_key=record_id
            )
            
            logger.info(f"Updated billing record: {record_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating billing record {record_id}: {str(e)}")
            raise 