from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv(dotenv_path='.env')

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider:
    """Factory class to create different LLM instances"""
    @staticmethod
    def get_model(provider: str = "gemini") -> BaseChatModel:
        if provider == "gemini":
            api_key = os.getenv('GOOGLE_API_KEY')
            return ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=api_key,
                temperature=0
            )
        elif provider == "anthropic":
            api_key = os.getenv('ANTHROPIC_API_KEY')
            return ChatAnthropic(
                anthropic_api_key='api_key',
                model="claude-3-haiku-20240307",
                temperature=0
            )
        elif provider == "openai":
            api_key = os.getenv('OPENAI_API_KEY')
            return ChatOpenAI(
                api_key=api_key,
                model="gpt-3.5-turbo",
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

class Agent:
    def __init__(self, medical_report=None, role=None, extra_info=None, provider="gemini"):
        self.medical_report = medical_report
        self.role = role
        self.extra_info = extra_info
        self.prompt_template = self.create_prompt_template()
        self.model = ModelProvider.get_model(provider)

    def create_prompt_template(self):
        if self.role == "MultidisciplinaryTeam":
            template = f"""
                Act like a multidisciplinary team of healthcare professionals.
                You will receive a medical report of a patient visited by a Cardiologist, Psychologist, and Pulmonologist.
                Task: Review the reports, analyze them, and come up with a list of 3 possible health issues of the patient.
                Just return a list of bullet points of 3 possible health issues of the patient and for each issue provide the reason.

                Cardiologist Report: {self.extra_info.get('cardiologist_report', '')}
                Psychologist Report: {self.extra_info.get('psychologist_report', '')}
                Pulmonologist Report: {self.extra_info.get('pulmonologist_report', '')}
            """
        else:
            templates = {
                "Cardiologist": """
                    Act like a cardiologist. You will receive a medical report of a patient.
                    Task: Review the patient's cardiac workup, including ECG, blood tests, Holter monitor results, and echocardiogram.
                    Recommendation: Provide possible causes of symptoms and recommended next steps.
                    Medical Report: {medical_report}
                """,
                "Psychologist": """
                    Act like a psychologist. You will receive a patient's report.
                    Task: Provide a psychological assessment of the patient.
                    Recommendation: Identify mental health issues and recommended next steps.
                    Patient's Report: {medical_report}
                """,
                "Pulmonologist": """
                    Act like a pulmonologist. You will receive a patient's report.
                    Task: Provide a pulmonary assessment of the patient.
                    Recommendation: Identify respiratory issues and recommended next steps.
                    Patient's Report: {medical_report}
                """
            }
            template = templates.get(self.role, "")
        return PromptTemplate.from_template(template)

    def run(self):
        logger.info(f"{self.role} is running with {type(self.model).__name__}...")
        try:
            prompt = self.prompt_template.format(medical_report=self.medical_report)
            response = self.model.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error occurred with {type(self.model).__name__}:", exc_info=True)
            return None

# Specialized agents
class Cardiologist(Agent):
    def __init__(self, medical_report, provider="gemini"):
        super().__init__(medical_report, "Cardiologist", provider=provider)

class Psychologist(Agent):
    def __init__(self, medical_report, provider="gemini"):
        super().__init__(medical_report, "Psychologist", provider=provider)

class Pulmonologist(Agent):
    def __init__(self, medical_report, provider="gemini"):
        super().__init__(medical_report, "Pulmonologist", provider=provider)

class MultidisciplinaryTeam(Agent):
    def __init__(self, cardiologist_report, psychologist_report, pulmonologist_report, provider="gemini"):
        extra_info = {
            "cardiologist_report": cardiologist_report,
            "psychologist_report": psychologist_report,
            "pulmonologist_report": pulmonologist_report
        }
        super().__init__(role="MultidisciplinaryTeam", extra_info=extra_info, provider=provider)
