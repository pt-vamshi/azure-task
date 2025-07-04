from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime

from config import Config
from models import BillingRecord, BillingResponse, ArchiveResponse
from archival_service import ArchivalService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Billing Records API with Archival",
    description="API for managing billing records with automatic archival to Azure Blob Storage",
    version="1.0.0"
)

# Initialize archival service
archival_service = ArchivalService()

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/billing/{record_id}", response_model=BillingResponse)
async def get_billing_record(record_id: str):
    """
    Retrieve a billing record by ID from either Cosmos DB or archived storage
    """
    try:
        record_data = archival_service.get_billing_record(record_id)
        
        # Determine the source
        cosmos_record = archival_service.cosmos_client.get_billing_record(record_id)
        source = "cosmos_db" if cosmos_record else "blob_storage"
        
        return BillingResponse(
            success=True,
            data=BillingRecord(**record_data),
            message="Billing record retrieved successfully",
            source=source
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving billing record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/billing", response_model=BillingResponse)
async def create_billing_record(record: BillingRecord):
    """
    Create a new billing record in Cosmos DB
    """
    try:
        # Generate ID if not provided
        if not record.id:
            record.id = str(uuid.uuid4())
        
        # Set creation timestamp if not provided
        if not record.created_at:
            record.created_at = datetime.utcnow()
        
        success = archival_service.cosmos_client.create_billing_record(record)
        
        if success:
            return BillingResponse(
                success=True,
                data=record,
                message="Billing record created successfully",
                source="cosmos_db"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create billing record")
            
    except Exception as e:
        logger.error(f"Error creating billing record: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/billing/{record_id}", response_model=BillingResponse)
async def update_billing_record(record_id: str, updates: Dict[str, Any]):
    """
    Update an existing billing record
    """
    try:
        # First check if record exists
        existing_record = archival_service.get_billing_record(record_id)
        if not existing_record:
            raise HTTPException(status_code=404, detail="Billing record not found")
        
        success = archival_service.cosmos_client.update_billing_record(record_id, updates)
        
        if success:
            # Get updated record
            updated_record = archival_service.get_billing_record(record_id)
            return BillingResponse(
                success=True,
                data=BillingRecord(**updated_record),
                message="Billing record updated successfully",
                source="cosmos_db"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update billing record")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating billing record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/billing/{record_id}")
async def delete_billing_record(record_id: str):
    """
    Delete a billing record
    """
    try:
        # Check if record exists
        existing_record = archival_service.get_billing_record(record_id)
        if not existing_record:
            raise HTTPException(status_code=404, detail="Billing record not found")
        
        # Delete from Cosmos DB
        cosmos_deleted = archival_service.cosmos_client.delete_record(record_id)
        
        # Delete from blob storage if it exists there
        blob_deleted = archival_service.blob_client.delete_billing_record(record_id)
        
        if cosmos_deleted or blob_deleted:
            return {"success": True, "message": "Billing record deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete billing record")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting billing record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/archive", response_model=ArchiveResponse)
async def trigger_archival(background_tasks: BackgroundTasks):
    """
    Trigger the archival process for old records
    """
    try:
        # Run archival in background
        background_tasks.add_task(archival_service.archive_old_records)
        
        return ArchiveResponse(
            success=True,
            archived_count=0,
            message="Archival process started in background"
        )
        
    except Exception as e:
        logger.error(f"Error triggering archival: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/archive/sync", response_model=ArchiveResponse)
async def trigger_sync_archival():
    """
    Trigger the archival process synchronously and return results
    """
    try:
        result = archival_service.archive_old_records()
        return result
        
    except Exception as e:
        logger.error(f"Error during sync archival: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/restore/{record_id}")
async def restore_record(record_id: str):
    """
    Restore a record from blob storage back to Cosmos DB
    """
    try:
        success = archival_service.restore_record(record_id)
        
        if success:
            return {"success": True, "message": f"Record {record_id} restored successfully"}
        else:
            raise HTTPException(status_code=404, detail="Record not found in archive or restoration failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats")
async def get_archival_stats():
    """
    Get statistics about the archival system
    """
    try:
        stats = archival_service.get_archival_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting archival stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True
    ) 