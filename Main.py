from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from Utils.Agents import Cardiologist, Psychologist, Pulmonologist, MultidisciplinaryTeam
import json
import os
import logging
from typing import Dict, Any
from pathlib import Path

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MedicalAnalyzer:
    def __init__(self, medical_report_path: str, provider:str):
        """
        Initialize the medical analyzer with a report path and AI provider.

        Args:
            medical_report_path (str): Path to the medical report file
            provider (str): AI provider to use ("gemini", "anthropic", or "openai")
        """
        self.medical_report_path = Path(medical_report_path)
        self.provider = provider
        self.responses: Dict[str, Any] = {}

        # Ensure required directories exist
        self.results_dir = Path("Results")
        self.results_dir.mkdir(exist_ok=True)

        # Load environment variables
        load_dotenv(dotenv_path='.env')

        # Read medical report
        self.medical_report = self._read_medical_report()

    def _read_medical_report(self) -> str:
        """Read and return the medical report content."""
        try:
            with open(self.medical_report_path, "r", encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"Medical report not found at {self.medical_report_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading medical report: {str(e)}")
            raise

    def _get_response(self, agent_name: str, agent: Any) -> tuple:
        """Get response from an agent."""
        try:
            logger.info(f"Getting response from {agent_name}")
            response = agent.run()
            if response is None:
                raise Exception(f"No response received from {agent_name}")
            return agent_name, response
        except Exception as e:
            logger.error(f"Error getting response from {agent_name}: {str(e)}")
            return agent_name, f"Error: {str(e)}"

    def analyze(self) -> Dict[str, str]:
        """Run the analysis using all agents."""
        # Initialize agents with specified provider
        roles = ["Cardiologist", "Psychologist", "Pulmonologist"]
        agents = {
            role: globals()[role](self.medical_report, provider=self.provider)
            for role in roles
        }

        # Run agents concurrently
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._get_response, name, agent): name
                for name, agent in agents.items()
            }

            for future in as_completed(futures):
                agent_name, response = future.result()
                self.responses[agent_name] = response

        # Run multidisciplinary team analysis
        team_agent = MultidisciplinaryTeam(
            cardiologist_report=self.responses["Cardiologist"],
            psychologist_report=self.responses["Psychologist"],
            pulmonologist_report=self.responses["Pulmonologist"],
            provider=self.provider
        )

        final_diagnosis = team_agent.run()
        self.responses["Final_Diagnosis"] = final_diagnosis

        return self.responses

    def save_results(self, path:str) -> None:
        """Save analysis results to files."""

        path = "final_diagnosis-" + path + ".txt"
        try:
            # Save final diagnosis to text file
            diagnosis_path = self.results_dir / path
            with open(diagnosis_path, "w", encoding='utf-8') as f:
                f.write("### Final Diagnosis:\n\n" + self.responses["Final_Diagnosis"])

            # Save all responses to JSON file
            json_path = self.results_dir / "all_responses.json"
            with open(json_path, "w", encoding='utf-8') as f:
                json.dump(self.responses, f, indent=4)

            logger.info(f"Results saved to {self.results_dir}")
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise

def main():
    medical_report_path="Medical_Reports/"
    # Input the
    details_of_patient = "112233-John-Davis"
    medical_report_path = medical_report_path + details_of_patient + ".txt"
    try:
        # Initialize the analyzer
        analyzer = MedicalAnalyzer(
            medical_report_path,
            provider="gemini"  # or "anthropic" or "openai"
        )

        # Run the analysis
        responses = analyzer.analyze()

        # Save the results
        analyzer.save_results(details_of_patient)

        logger.info("Analysis completed successfully")
        return responses

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
