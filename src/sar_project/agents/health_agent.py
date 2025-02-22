from src.sar_project.agents.base_agent import SARBaseAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.parse
import re
import json
import openai

class HealthAgent(SARBaseAgent):
    def __init__(self, name="health_specialist"):
        super().__init__(
            name=name,
            role="Health Specialist",
            system_message="""You are a health specialist for SAR operations. Your responsibilities include:
            1. Assembling a general health profile of the missing person using available records.
            2. Extrapolating current health status based on the assembled profile.
            3. Analyzing medication data to assess potential drug interactions and effects.
            4. Evaluating environmental impacts on the subject’s health.
            5. Estimating survival time under current conditions.
            6. Planning appropriate medical resources for rescue operations.
            7. Assessing health risks that may arise during SAR operations.
            8. Generating medical advice for SAR teams in the field.
            9. Providing information on drug, food, and disease interactions.
            10. Updating and retrieving the current mission status.
            """
        )
        # Optionally maintain state for assembled profiles or statuses
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/91.0.4472.124 Safari/537.36")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.health_profiles = {}
        self.status_reports = {}
        
        
    def process_request(self, message):
        """
        Process incoming health-related requests. Expected message keys include:
        - "assemble_profile": with patient data dictionary under key "patient_data"
        - "extrapolate_status": with profile dictionary under key "profile"
        - "analyze_medication": with medication data under key "medication_data"
        - "evaluate_environment": with environmental data under key "environment_data" 
                                  and optionally patient data under "patient_data"
        - "estimate_survival": with "profile" and "environment_data"
        - "plan_resources": with "profile" and "current_status"
        - "assess_health_risk": with "profile" and "environment_data"
        - "generate_medical_advice": with "profile", "environment_data", and optionally "survival_estimation"
        - "get_drug_interactions": with "drug_name"
        - "get_food_interactions": with "drug_name"
        - "get_disease_interactions": with "drug_name"
        - "get_all_interactions": with "drug_name"
        - "update_status": with "status"
        - "get_status": with no additional data
        """
        try:
            if "assemble_profile" in message:
                return self.assemble_health_profile(message["patient_data"])
            elif "extrapolate_status" in message:
                return self.extrapolate_current_status(message["profile"])
            elif "analyze_medication" in message:
                return self.analyze_medication(message["medication_data"])
            elif "evaluate_environment" in message:
                patient_data = message.get("patient_data", {})
                return self.evaluate_environment(message["environment_data"], patient_data)
            elif "estimate_survival" in message:
                return self.estimate_survival_time(message["profile"], message["environment_data"])
            elif "plan_resources" in message:
                return self.plan_medical_resources(message["profile"], message["current_status"])
            elif "assess_health_risk" in message:
                return self.assess_health_risk(message["profile"], message["environment_data"])
            elif "generate_medical_advice" in message:
                survival_estimation = message.get("survival_estimation", {})
                return self.generate_medical_advice(message["profile"], message["environment_data"], survival_estimation)
            elif "get_drug_interactions" in message:
                slug = self.get_interactions_slug(message["drug_name"])
                return self.get_drug_interactions(slug)
            elif "get_food_interactions" in message:            
                slug = self.get_interactions_slug(message["drug_name"])
                return {"food_interactions": self.get_food_interactions_text(slug)}
            elif "get_disease_interactions" in message:
                slug = self.get_interactions_slug(message["drug_name"])
                return {"disease_interactions": self.get_disease_interactions_text(slug)}
            elif "get_all_interactions" in message:
                return self.get_all_interactions(message["drug_name"])
            elif "update_status" in message:
                return self.update_status(message["status"])
            elif "get_status" in message:
                return {"status": self.get_status()}
            else:
                return {"error": "Unknown request type"}
        except Exception as e:
            return {"error": str(e)}

    def assemble_health_profile(self, patient_data):
        """
        Create a general health profile for the missing person.
        Expected patient_data format:
        {
            "id": "patient123",
            "age": 45,
            "medical_history": ["hypertension", "diabetes"],
            "allergies": ["penicillin"],
            "current_conditions": ["asthma"],
            "medications": [
                {"name": "DrugA", "dosage": "50mg", "frequency": "daily"}
            ]
        }
        """
        profile = {
            "id": patient_data.get("id", "unknown"),
            "age": patient_data.get("age", "unknown"),
            "medical_history": patient_data.get("medical_history", []),
            "allergies": patient_data.get("allergies", []),
            "current_conditions": patient_data.get("current_conditions", []),
            "medications": patient_data.get("medications", []),
        }
        # Save profile in the agent's state (if needed)
        self.health_profiles[profile["id"]] = profile
        return {"profile": profile, "message": "Health profile assembled successfully."}

    def extrapolate_current_status(self, profile):
        """
        Predict the current health status based on the health profile.
        Uses a simple logic: if critical conditions are present, status is 'critical',
        otherwise 'stable'. Also calculates a simulated health score.
        """
        conditions = profile.get("current_conditions", [])
        # Determine status based on the presence of severe conditions
        if any(cond in ["severe_injury", "cardiac_arrest", "respiratory_failure"] for cond in conditions):
            status = "critical"
        else:
            status = "stable"
        # Simulate a health score (this is an arbitrary calculation)
        age = profile.get("age", 50) if isinstance(profile.get("age", 50), (int, float)) else 50
        health_score = max(0, 100 - (age * 0.5))
        result = {"current_status": status, "health_score": health_score}
        # Optionally store the status
        self.status_reports[profile.get("id", "unknown")] = result
        return result

    def analyze_medication(self, medication_data):
        """
        Assess the impact of medication access or lack thereof.
        Expected medication_data format: a list of medication dicts, for example:
        [
            {"name": "DrugA", "dosage": "50mg", "frequency": "daily"},
            {"name": "DrugB", "dosage": "10mg", "frequency": "twice_daily"}
        ]
        """
        interactions = []
        if len(medication_data) > 1:
            # Simplified example: warn about potential interactions when multiple medications are present.
            interactions.append("Potential drug interactions detected among prescribed medications.")
        else:
            interactions.append("No significant drug interactions detected.")
        return {"medication_analysis": interactions}

    def evaluate_environment(self, environment_data, patient_data):
        """
        Evaluate environmental effects on health.
        Expected environment_data format:
        {
            "temperature": 22,       # in Celsius
            "humidity": 60,          # percentage
            "pollution_level": 80,   # Air Quality Index or similar metric
            "altitude": 500          # in meters
        }
        The patient_data can be used to check for vulnerabilities (e.g., asthma).
        """
        impact = "minimal"
        # Check for high pollution impact on a patient with respiratory issues
        if environment_data.get("pollution_level", 0) > 100 and "asthma" in patient_data.get("current_conditions", []):
            impact = "high"
        # Check for extreme temperature conditions
        elif environment_data.get("temperature", 22) > 35 or environment_data.get("temperature", 22) < 5:
            impact = "moderate"
        return {"environmental_impact": impact, "details": environment_data}

    def estimate_survival_time(self, profile, environment_data):
        """
        Estimate survival time under current conditions.
        This function uses a simple model:
        - Base survival time is 48 hours.
        - If health status is critical, reduce to 24 hours.
        - Adjust based on extreme environmental conditions.
        """
        base_time = 48  # hours
        status_result = self.extrapolate_current_status(profile)
        if status_result.get("current_status") == "critical":
            base_time = 24

        # Adjust for environmental extremes (e.g., very high or low temperatures)
        temperature = environment_data.get("temperature", 22)
        if temperature > 40 or temperature < 0:
            base_time *= 0.75

        return {"estimated_survival_hours": base_time}

    def plan_medical_resources(self, profile, current_status):
        """
        Recommend medical resources for SAR operations.
        Expects:
        - profile: as assembled from patient data.
        - current_status: output from extrapolate_current_status.
        """
        resources = []
        # Recommend advanced support if the patient is in a critical state
        if current_status.get("current_status") == "critical":
            resources.append("advanced life support equipment")
        else:
            resources.append("basic first aid kit")
        
        # Additional resources for elderly patients
        age = profile.get("age", 30)
        if isinstance(age, (int, float)) and age > 60:
            resources.append("geriatric care supplies")
        
        return {"recommended_resources": resources}

    def assess_health_risk(self, profile, environment_data):
        """
        Identify potential health risks during SAR operations by combining
        patient health profile and environmental hazards.
        """
        risks = []
        status = self.extrapolate_current_status(profile).get("current_status", "stable")
        if status == "critical":
            risks.append("High risk due to critical health status.")
        if environment_data.get("pollution_level", 0) > 150:
            risks.append("High risk due to extreme environmental pollution.")
        return {"health_risks": risks}

    def generate_medical_advice(self, profile, environment_data, survival_estimation):
        """
        Generate medical advice for SAR teams.
        Combines the health profile, environmental data, and survival time estimation.
        """
        advice = "Monitor the patient's condition continuously and prepare for rapid intervention."
        risks_info = self.assess_health_risk(profile, environment_data).get("health_risks", [])
        if risks_info:
            advice += " Identified risks include: " + ", ".join(risks_info)
        survival_hours = survival_estimation.get("estimated_survival_hours", 48)
        if survival_hours < 24:
            advice += " Immediate evacuation is strongly recommended."
        return {"medical_advice": advice}

    def get_interactions_slug(self, drug_name):
        """
        Searches drugs.com for the given drug name (or alias) and extracts the interactions slug.

        For example, if the search is for "skyclarys" (also known as "omaveloxolone"),
        and the interactions link is:
            /drug-interactions/omaveloxolone,skyclarys.html
        this function returns:
            "omaveloxolone,skyclarys"

        Parameters:
            drug_name (str): The name or alias of the drug to search for.

        Returns:
            str: The extracted interactions slug.

        Raises:
            Exception: If the search fails or the interactions link cannot be found/parsed.
        """
        base_search_url = "https://www.drugs.com/search.php"
        params = {"searchterm": drug_name}
        url = f"{base_search_url}?{urllib.parse.urlencode(params)}"
        
        self.driver.get(url)
        
        try:
            # Wait until an anchor tag with href containing '/drug-interactions/' is present.
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/drug-interactions/']"))
            )
        except Exception:
            raise Exception(f"Failed to retrieve search results for '{drug_name}'.")
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        interaction_link = soup.find("a", href=lambda x: x and "/drug-interactions/" in x)
        if not interaction_link:
            raise Exception(f"No drug interactions link found for '{drug_name}'.")
        
        href = interaction_link.get("href")
        match = re.search(r"/drug-interactions/([^/]+)\.html", href)
        if match:
            return match.group(1)
        else:
            raise Exception(f"Could not parse interaction slug from link: {href}")
    
    def _get_interaction_drugs(self, slug, filter_value):
        """
        Helper function that scrapes the interactions page for a given filter value.

        Parameters:
            slug (str): The interactions slug extracted from the search page.
            filter_value (int): The filter parameter (e.g., 3 for major, 2 for moderate).

        Returns:
            set: A set of drug names found in the interactions list.
        """
        url = f"https://www.drugs.com/drug-interactions/{slug}-index.html?filter={filter_value}"
        self.driver.get(url)
        
        try:
            # Wait until the interactions list loads.
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.interactions.ddc-list-column-2"))
            )
        except Exception:
            raise Exception(f"Failed to retrieve interactions page for slug '{slug}' with filter {filter_value}.")
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        drug_names = set()
        for ul in soup.find_all("ul", class_="interactions ddc-list-column-2"):
            for li in ul.find_all("li"):
                a_tag = li.find("a")
                if a_tag and a_tag.text:
                    drug_names.add(a_tag.text.strip())
        return drug_names
    
    def get_drug_interactions(self, slug):
        """
        Scrapes the drug interactions page for the given slug for both major and moderate interactions.
        
        Parameters:
            slug (str): The interactions slug (e.g., "omaveloxolone,skyclarys").
            
        Returns:
            dict: A dictionary with two keys:
                - "major": list of drug names for major interactions (filter=3)
                - "moderate": list of drug names for moderate interactions (filter=2)
        """
        major_interactions = self._get_interaction_drugs(slug, 3)
        moderate_interactions = self._get_interaction_drugs(slug, 2)
        return {"major": list(major_interactions), "moderate": list(moderate_interactions)}
    
    def get_food_interactions_text(self, slug):
        """
        Scrapes the food interactions page from drugs.com for the given interactions slug.
        
        The URL used is:
            f"https://www.drugs.com/food-interactions/{slug}.html?professional=1"
            
        This function retrieves the entire text content of the section.

        Parameters:
            slug (str): The interactions slug (e.g., "omaveloxolone,skyclarys").
            
        Returns:
            str: The complete text content from the food interactions section.

        Raises:
            Exception: If the page cannot be retrieved or the required content is not found.
        """
        url = f"https://www.drugs.com/food-interactions/{slug}.html?professional=1"
        self.driver.get(url)
        
        try:
            # Wait until the food interactions reference div loads.
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.interactions-reference"))
            )
        except Exception:
            raise Exception(f"Failed to retrieve food interactions page for slug '{slug}'.")
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        interactions_div = soup.find("div", class_="interactions-reference")
        if not interactions_div:
            raise Exception("Could not locate the food interactions reference section on the page.")
        
        full_text = interactions_div.get_text(separator="\n", strip=True)
        return full_text
    
    def get_disease_interactions_text(self, slug):
        """
        Scrapes the disease interactions page from drugs.com for the given interactions slug.
        
        The URL used is:
            f"https://www.drugs.com/disease-interactions/{slug}.html?professional=1"
        
        This function retrieves the entire text content from the interactions section.

        Parameters:
            slug (str): The interactions slug (e.g., "omaveloxolone,skyclarys").
            
        Returns:
            str: The complete text content from the disease interactions section.

        Raises:
            Exception: If the page cannot be retrieved or the required content is not found.
        """
        url = f"https://www.drugs.com/disease-interactions/{slug}.html?professional=1"
        self.driver.get(url)
        
        try:
            # Wait until the disease interactions reference div loads.
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.interactions-reference"))
            )
        except Exception:
            raise Exception(f"Failed to retrieve disease interactions page for slug '{slug}'.")
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        interactions_div = soup.find("div", class_="interactions-reference")
        if not interactions_div:
            raise Exception("Could not locate the disease interactions reference section on the page.")
        
        full_text = interactions_div.get_text(separator="\n", strip=True)
        return full_text
    
    def close(self):
        """Clean up the Selenium webdriver."""
        self.driver.quit()


    def get_all_interactions(self, drug_name):
        """
        Looks up the provided drug name, retrieves its interactions slug, and returns all interactions.
        
        Returns a JSON-like dictionary with the following keys:
            - "drug_name": the input drug name
            - "slug": the extracted interactions slug
            - "drug_interactions": dictionary with "major" and "moderate" lists
            - "food_interactions": full text from the food interactions page
            - "disease_interactions": full text from the disease interactions page
        """
        slug = self.get_interactions_slug(drug_name)
        drug_interactions = self.get_drug_interactions(slug)
        food_interactions = self.get_food_interactions_text(slug)
        disease_interactions = self.get_disease_interactions_text(slug)
        
        return {
            "drug_name": drug_name,
            "slug": slug,
            "drug_interactions": drug_interactions,
            "food_interactions": food_interactions,
            "disease_interactions": disease_interactions
        }
        
    def extend_profile(self, profile_id, new_data):
        """
        Extend an existing health profile with new data.
        """       
        if profile_id in self.health_profiles:
            profile = self.health_profiles[profile_id]
            profile.update(new_data)
            return {"status": "updated", "new_profile": profile}
        else:
            return {"error": "Profile not found."}

        
    def prompt_with_profile_facts(self, profile_id, other_info="None"):
        """
        Prompts an OpenAI LLM with all known facts about a specific health profile.

        Parameters:
            profile_id (str): The ID of the profile to use in the prompt.

        Returns:
            dict: Result from the LLM with the generated response or an error message.
        """

        # Retrieve the health profile
        profile = self.health_profiles.get(profile_id)
        if not profile:
            return {"error": "Profile not found."}

        # Serialize profile to JSON for structured input
        known_facts = json.dumps(profile, indent=2)

        # Construct message content
        prompt = (
            f"You are a health specialist for SAR operations.\n"
            f"Known facts about the health profile:\n{known_facts}\n"
            f"Other information supplied:\n{other_info}\n"
            "Please provide an analysis or suggest next steps."
        )

        # Interact with the OpenAI model
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500
            )
            # Extract the text response
            generated_response = response['choices'][0]['message']['content'].strip()
            return {"response": generated_response}
        except Exception as e:
            return {"error": str(e)}

    def update_status(self, status):
        """Update the agent's mission status."""
        self.mission_status = status
        return {"status": "updated", "new_status": status}

    def get_status(self):
        """Return the current mission status."""
        return self.mission_status
