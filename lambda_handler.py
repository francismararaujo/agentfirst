"""Lambda handler entry point for AgentFirst2 MVP

This module serves as the entry point for AWS Lambda.
It imports and delegates to the main handler in app/lambda_handler.py
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entry point
    
    This function handles both sync and async operations by:
    1. Importing the main handler from app/
    2. Checking if the result is a coroutine
    3. Running async operations in event loop if needed
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Lambda response
    """
    try:
        # Import the main handler
        from app.main import app
        from mangum import Mangum
        
        # Create Mangum handler
        handler = Mangum(app, lifespan="off")
        
        # Call handler
        result = handler(event, context)
        
        # Check if result is a coroutine (async function)
        if asyncio.iscoroutine(result):
            # Run async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(result)
            finally:
                loop.close()
        
        logger.info(f"Lambda execution completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }),
            "headers": {"Content-Type": "application/json"}
        }