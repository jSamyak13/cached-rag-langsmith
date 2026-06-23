import sys
import logging
from crag_with_langsmith_tracing.backend.config.logging_config import setup_logging
from crag_with_langsmith_tracing.backend.pipeline.agent import run_query

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.info("Initializing CRAG pipeline CLI")
    
    while True:
        try:
            user_input = input(" : ").strip()
            if not user_input:
                continue
            if user_input.lower() == "exit":
                logger.info("Exiting CRAG pipeline CLI")
                break
            
            result = run_query(user_input, "0000")
            print(f"Answer: {result.get('answer')}")
            print(f"Sources: {result.get('sources')}")
        except KeyboardInterrupt:
            logger.info("Interrupted by user, exiting")
            break
        except Exception as e:
            logger.error(f"Unexpected error in input loop: {e}")

if __name__ == "__main__":
    main()
