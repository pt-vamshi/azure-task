import azure.functions as func
import logging
from datetime import datetime
import json

# Import our archival service
from archival_service import ArchivalService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(mytimer: func.TimerRequest) -> None:
    """
    Azure Function that runs on a schedule to archive old billing records
    """
    utc_timestamp = datetime.utcnow().replace(
        tzinfo=None
    ).isoformat()

    if mytimer.past_due:
        logger.warning('The timer is past due!')

    logger.info(f'Python timer trigger function ran at {utc_timestamp}')
    
    try:
        # Initialize archival service
        archival_service = ArchivalService()
        
        # Run the archival process
        result = archival_service.archive_old_records()
        
        # Log the results
        if result.success:
            logger.info(f"Archival completed successfully: {result.message}")
            logger.info(f"Records archived: {result.archived_count}")
        else:
            logger.error(f"Archival failed: {result.message}")
            
        # Return the result as JSON
        return func.HttpResponse(
            json.dumps({
                "success": result.success,
                "archived_count": result.archived_count,
                "message": result.message,
                "timestamp": utc_timestamp
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in archival function: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "archived_count": 0,
                "message": f"Archival function failed: {str(e)}",
                "timestamp": utc_timestamp
            }),
            status_code=500,
            mimetype="application/json"
        ) 