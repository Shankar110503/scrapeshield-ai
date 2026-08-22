import logging
from app.brightdata import BrightDataClient

logger = logging.getLogger("ScrapeHealer")

class AutoHealer:
    def __init__(self):
        self.client = BrightDataClient()

    def validate_extraction(self, data: dict, required_keys: list) -> list:
        """Checks if expected fields are missing or empty"""
        missing_keys = []
        if not data:
            return required_keys
        
        for key in required_keys:
            val = data.get(key)
            if val is None or val == "" or val == []:
                missing_keys.append(key)
        return missing_keys

    def auto_repair_loop(self, collector_id: str, target_url: str, required_fields: list) -> dict:
        """Runs scraper, detects breakage, and heals if necessary"""
        data = self.client.run_scraper(collector_id, target_url)
        failed_fields = self.validate_extraction(data, required_fields)
        
        if not failed_fields:
            logger.info("Data extracted successfully. Scraper is healthy.")
            return {"status": "HEALTHY", "data": data}

        logger.warning(f"Fields missing/broken: {failed_fields}. Initiating self-healing...")
        heal_prompt = f"The site layout changed. Please re-extract these missing fields accurately: {', '.join(failed_fields)}"
        
        success = self.client.heal_scraper(collector_id, heal_prompt)
        
        if success:
            logger.info("Self-healing successful. Re-running scraper...")
            repaired_data = self.client.run_scraper(collector_id, target_url)
            return {"status": "REPAIRED", "data": repaired_data, "healed_fields": failed_fields}
        else:
            return {"status": "FAILED", "data": data, "error": "Self-healing execution failed."}
            
