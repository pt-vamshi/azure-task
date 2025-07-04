from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from config import Config
from cosmos_client import CosmosDBClient
from blob_client import BlobStorageClient
from models import ArchiveIndex, ArchiveResponse, BillingRecord

logger = logging.getLogger(__name__)

class ArchivalService:
    def __init__(self):
        self.cosmos_client = CosmosDBClient()
        self.blob_client = BlobStorageClient()
    
    def archive_old_records(self) -> ArchiveResponse:
        """
        Main archival process that moves records older than the threshold from Cosmos DB to Blob Storage
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=Config.ARCHIVAL_DAYS_THRESHOLD)
            cutoff_date_str = cutoff_date.isoformat()
            
            logger.info(f"Starting archival process for records older than: {cutoff_date_str}")
            
            # Get records to archive
            records_to_archive = self.cosmos_client.get_records_to_archive(cutoff_date_str)
            
            if not records_to_archive:
                logger.info("No records found for archival")
                return ArchiveResponse(
                    success=True,
                    archived_count=0,
                    message="No records found for archival"
                )
            
            archived_count = 0
            
            # Process records in batches
            for i in range(0, len(records_to_archive), Config.BATCH_SIZE):
                batch = records_to_archive[i:i + Config.BATCH_SIZE]
                batch_archived = self._archive_batch(batch)
                archived_count += batch_archived
                
                logger.info(f"Processed batch {i//Config.BATCH_SIZE + 1}, archived {batch_archived} records")
            
            logger.info(f"Archival process completed. Total records archived: {archived_count}")
            
            return ArchiveResponse(
                success=True,
                archived_count=archived_count,
                message=f"Successfully archived {archived_count} records"
            )
            
        except Exception as e:
            logger.error(f"Error during archival process: {str(e)}")
            return ArchiveResponse(
                success=False,
                archived_count=0,
                message=f"Archival process failed: {str(e)}"
            )
    
    def _archive_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Archive a batch of records
        """
        archived_count = 0
        
        for record in records:
            try:
                record_id = record.get('id')
                if not record_id:
                    logger.warning("Record missing ID, skipping")
                    continue
                
                # Upload to blob storage
                blob_path = self.blob_client.upload_billing_record(record_id, record)
                
                # Create archive index
                archive_index = ArchiveIndex(
                    id=record_id,
                    blob_path=blob_path,
                    archived_at=datetime.utcnow(),
                    original_created_at=datetime.fromisoformat(record.get('created_at', datetime.utcnow().isoformat()))
                )
                
                self.cosmos_client.create_archive_index(archive_index)
                
                # Delete from Cosmos DB
                self.cosmos_client.delete_record(record_id)
                
                archived_count += 1
                logger.debug(f"Successfully archived record: {record_id}")
                
            except Exception as e:
                logger.error(f"Error archiving record {record.get('id', 'unknown')}: {str(e)}")
                # Continue with next record instead of failing the entire batch
                continue
        
        return archived_count
    
    def get_billing_record(self, record_id: str) -> Dict[str, Any]:
        """
        Retrieve a billing record from either Cosmos DB or Blob Storage
        """
        # First try Cosmos DB
        record = self.cosmos_client.get_billing_record(record_id)
        if record:
            return record
        
        # If not found in Cosmos DB, check archive index
        archive_index = self.cosmos_client.get_archive_index(record_id)
        if archive_index:
            # Retrieve from blob storage using the stored path
            record = self.blob_client.download_billing_record_by_path(archive_index['blob_path'])
            if record:
                return record
        
        # If still not found, try direct blob lookup (fallback)
        record = self.blob_client.download_billing_record(record_id)
        if record:
            return record
        
        # Record not found anywhere
        raise ValueError(f"Billing record not found: {record_id}")
    
    def restore_record(self, record_id: str) -> bool:
        """
        Restore a record from blob storage back to Cosmos DB
        """
        try:
            # Get archive index
            archive_index = self.cosmos_client.get_archive_index(record_id)
            if not archive_index:
                logger.warning(f"No archive index found for record: {record_id}")
                return False
            
            # Download from blob storage
            record = self.blob_client.download_billing_record_by_path(archive_index['blob_path'])
            if not record:
                logger.warning(f"Record not found in blob storage: {record_id}")
                return False
            
            # Create in Cosmos DB
            self.cosmos_client.create_billing_record(BillingRecord(**record))
            
            # Delete from blob storage
            self.blob_client.delete_billing_record(record_id)
            
            # Delete archive index
            self.cosmos_client.delete_record(record_id)  # This deletes from archive index container
            
            logger.info(f"Successfully restored record: {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring record {record_id}: {str(e)}")
            return False
    
    def get_archival_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the archival system
        """
        try:
            # Count records in Cosmos DB
            cosmos_count = len(list(self.cosmos_client.container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            )))
            
            # Count archive index entries
            archive_count = len(list(self.cosmos_client.archive_index_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            )))
            
            # List archived blobs
            archived_blobs = self.blob_client.list_archived_records()
            
            return {
                "cosmos_db_records": cosmos_count,
                "archived_records": archive_count,
                "blob_storage_files": len(archived_blobs),
                "archival_threshold_days": Config.ARCHIVAL_DAYS_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Error getting archival stats: {str(e)}")
            return {"error": str(e)} 