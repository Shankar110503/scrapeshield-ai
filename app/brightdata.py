import json
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrightDataCLI")

class BrightDataClient:
    def __init__(self):
        self.cli_prefix = ["npx", "-p", "@brightdata/cli", "bdata"]

    def _run_command(self, cmd_args):
        full_cmd = self.cli_prefix + cmd_args
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"CLI Error: {e.stderr}")
            raise RuntimeError(f"BrightData CLI failed: {e.stderr}")

    def create_scraper(self, url: str, prompt: str) -> str:
        """Creates a new scraper and returns Collector ID (c_*)"""
        logger.info(f"Creating scraper for {url}...")
        output = self._run_command(["scraper", "create", url, prompt])
        for line in output.split("\n"):
            if "c_" in line:
                collector_id = line.strip().split()[-1]
                return collector_id
        return output

    def run_scraper(self, collector_id: str, url: str) -> dict:
        """Runs the scraper and returns JSON data"""
        logger.info(f"Running scraper {collector_id} against {url}...")
        output = self._run_command(["scraper", "run", collector_id, url, "--pretty"])
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"raw_output": output}

    def heal_scraper(self, collector_id: str, heal_prompt: str) -> bool:
        """Heals an existing scraper with a plain language description"""
        logger.info(f"Healing scraper {collector_id} with prompt: '{heal_prompt}'...")
        try:
            self._run_command(["scraper", "heal", collector_id, heal_prompt])
            return True
        except Exception as e:
            logger.error(f"Healing failed: {str(e)}")
            return False
            
