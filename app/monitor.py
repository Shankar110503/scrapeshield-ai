import time
import logging
from app.healer import AutoHealer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScrapeMonitor")

class ScraperMonitor:
    def __init__(self, collector_id: str, target_url: str, required_fields: list):
        self.collector_id = collector_id
        self.target_url = target_url
        self.required_fields = required_fields
        self.healer = AutoHealer()

    def start_monitoring(self, interval_seconds: int = 3600):
        """Monitors the scraper at regular intervals."""
        logger.info(f"Starting continuous monitoring for {self.collector_id} every {interval_seconds} seconds...")
        try:
            while True:
                logger.info("Executing scheduled health check...")
                result = self.healer.auto_repair_loop(
                    self.collector_id, 
                    self.target_url, 
                    self.required_fields
                )
                logger.info(f"Health Check Status: {result.get('status')}")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user.")
            
