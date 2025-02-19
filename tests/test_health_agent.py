import pytest
from unittest.mock import patch
from sar_project.agents.health_agent import HealthAgent


class TestHealthAgent:
    @pytest.fixture
    def health_agent(self):
        return HealthAgent()


    ## Tests for assemble_health_profile

    def test_assemble_health_profile_valid(self, health_agent):
        patient_data = {
            "id": "patient123",
            "age": 45,
            "medical_history": ["hypertension", "diabetes"],
            "allergies": ["penicillin"],
            "current_conditions": ["asthma"],
            "medications": [{"name": "DrugA", "dosage": "50mg", "frequency": "daily"}]
        }
        result = health_agent.assemble_health_profile(patient_data)
        profile = result.get("profile", {})
        assert profile["id"] == "patient123"
        assert profile["age"] == 45
        assert profile["medical_history"] == ["hypertension", "diabetes"]
        assert "Health profile assembled successfully." in result.get("message")


    def test_assemble_health_profile_missing_fields(self, health_agent):
        patient_data = {"id": "patient456"}
        result = health_agent.assemble_health_profile(patient_data)
        profile = result.get("profile", {})
        assert profile["id"] == "patient456"
        assert profile.get("age") == "unknown"
        assert profile.get("medical_history") == []
        assert profile.get("allergies") == []
        assert profile.get("current_conditions") == []
        assert profile.get("medications") == []


    def test_assemble_health_profile_storage(self, health_agent):
        patient_data = {"id": "patient789", "age": 30}
        result = health_agent.assemble_health_profile(patient_data)
        profile_id = result.get("profile", {}).get("id")
        assert profile_id in health_agent.health_profiles
        assert health_agent.health_profiles[profile_id] == result["profile"]


    ### Tests for extrapolate_current_status

    def test_extrapolate_current_status_stable(self, health_agent):
        profile = {
            "id": "patient123",
            "age": 40,
            "current_conditions": ["asthma"]
        }
        result = health_agent.extrapolate_current_status(profile)
        assert result["current_status"] == "stable"
        expected_score = max(0, 100 - (40 * 0.5))
        assert result["health_score"] == expected_score


    def test_extrapolate_current_status_critical(self, health_agent):
        profile = {
            "id": "patientCritical",
            "age": 50,
            "current_conditions": ["severe_injury"]
        }
        result = health_agent.extrapolate_current_status(profile)
        assert result["current_status"] == "critical"


    def test_extrapolate_current_status_missing_age(self, health_agent):
        profile = {
            "id": "patientNoAge",
            "current_conditions": []
        }
        result = health_agent.extrapolate_current_status(profile)
        assert result["health_score"] == 75


    ### Tests for analyze_medication

    def test_analyze_medication_single(self, health_agent):
        medications = [{"name": "DrugA", "dosage": "50mg", "frequency": "daily"}]
        result = health_agent.analyze_medication(medications)
        analysis = result.get("medication_analysis", [])
        assert "No significant drug interactions detected." in analysis


    def test_analyze_medication_multiple(self, health_agent):
        medications = [
            {"name": "DrugA", "dosage": "50mg", "frequency": "daily"},
            {"name": "DrugB", "dosage": "10mg", "frequency": "twice_daily"}
        ]
        result = health_agent.analyze_medication(medications)
        analysis = result.get("medication_analysis", [])
        assert "Potential drug interactions detected among prescribed medications." in analysis


    def test_analyze_medication_empty(self, health_agent):
        medications = []
        result = health_agent.analyze_medication(medications)
        analysis = result.get("medication_analysis", [])
        assert "No significant drug interactions detected." in analysis


    ### Tests for evaluate_environment

    def test_evaluate_environment_high_pollution(self, health_agent):
        environment_data = {
            "temperature": 22,
            "humidity": 50,
            "pollution_level": 120,
            "altitude": 300
        }
        patient_data = {"current_conditions": ["asthma"]}
        result = health_agent.evaluate_environment(environment_data, patient_data)
        assert result["environmental_impact"] == "high"


    def test_evaluate_environment_extreme_temperature(self, health_agent):
        environment_data = {
            "temperature": 40,
            "humidity": 50,
            "pollution_level": 50,
            "altitude": 300
        }
        patient_data = {"current_conditions": []}
        result = health_agent.evaluate_environment(environment_data, patient_data)
        assert result["environmental_impact"] == "moderate"


    def test_evaluate_environment_normal(self, health_agent):
        environment_data = {
            "temperature": 22,
            "humidity": 50,
            "pollution_level": 50,
            "altitude": 300
        }
        patient_data = {"current_conditions": []}
        result = health_agent.evaluate_environment(environment_data, patient_data)
        assert result["environmental_impact"] == "minimal"


    ### Tests for estimate_survival_time

    def test_estimate_survival_stable_normal(self, health_agent):
        profile = {"id": "patient1", "age": 30, "current_conditions": []}
        environment_data = {"temperature": 22}
        result = health_agent.estimate_survival_time(profile, environment_data)
        assert result["estimated_survival_hours"] == 48


    def test_estimate_survival_critical_normal(self, health_agent):
        profile = {"id": "patient2", "age": 30, "current_conditions": ["cardiac_arrest"]}
        environment_data = {"temperature": 22}
        result = health_agent.estimate_survival_time(profile, environment_data)
        assert result["estimated_survival_hours"] == 24


    def test_estimate_survival_stable_extreme(self, health_agent):
        profile = {"id": "patient3", "age": 30, "current_conditions": []}
        environment_data = {"temperature": 45}
        result = health_agent.estimate_survival_time(profile, environment_data)
        assert result["estimated_survival_hours"] == 36


    ### Tests for plan_medical_resources

    def test_plan_resources_non_critical_young(self, health_agent):
        profile = {"id": "patient1", "age": 30}
        current_status = {"current_status": "stable"}
        result = health_agent.plan_medical_resources(profile, current_status)
        resources = result.get("recommended_resources", [])
        assert "basic first aid kit" in resources
        assert "advanced life support equipment" not in resources


    def test_plan_resources_non_critical_elderly(self, health_agent):
        profile = {"id": "patient2", "age": 70}
        current_status = {"current_status": "stable"}
        result = health_agent.plan_medical_resources(profile, current_status)
        resources = result.get("recommended_resources", [])
        assert "basic first aid kit" in resources
        assert "geriatric care supplies" in resources


    def test_plan_resources_critical(self, health_agent):
        profile = {"id": "patient3", "age": 30}
        current_status = {"current_status": "critical"}
        result = health_agent.plan_medical_resources(profile, current_status)
        resources = result.get("recommended_resources", [])
        assert "advanced life support equipment" in resources


    ### Tests for assess_health_risk

    def test_assess_health_risk_stable_low_pollution(self, health_agent):
        profile = {"id": "patient1", "age": 30, "current_conditions": []}
        environment_data = {"pollution_level": 50}
        result = health_agent.assess_health_risk(profile, environment_data)
        risks = result.get("health_risks", [])
        assert risks == []


    def test_assess_health_risk_critical(self, health_agent):
        profile = {"id": "patient2", "age": 30, "current_conditions": ["severe_injury"]}
        environment_data = {"pollution_level": 50}
        result = health_agent.assess_health_risk(profile, environment_data)
        risks = result.get("health_risks", [])
        assert "High risk due to critical health status." in risks


    def test_assess_health_risk_high_pollution(self, health_agent):
        profile = {"id": "patient3", "age": 30, "current_conditions": []}
        environment_data = {"pollution_level": 200}
        result = health_agent.assess_health_risk(profile, environment_data)
        risks = result.get("health_risks", [])
        assert "High risk due to extreme environmental pollution." in risks


    ### Tests for generate_medical_advice

    def test_generate_medical_advice_stable(self, health_agent):
        profile = {"id": "patient1", "age": 30, "current_conditions": []}
        environment_data = {"temperature": 22, "pollution_level": 50}
        survival_estimation = {"estimated_survival_hours": 48}
        result = health_agent.generate_medical_advice(profile, environment_data, survival_estimation)
        advice = result.get("medical_advice", "")
        assert "Monitor the patient's condition continuously" in advice
        assert "Immediate evacuation is strongly recommended." not in advice


    def test_generate_medical_advice_critical(self, health_agent):
        profile = {"id": "patient2", "age": 30, "current_conditions": ["severe_injury"]}
        environment_data = {"temperature": 22, "pollution_level": 50}
        survival_estimation = {"estimated_survival_hours": 24}
        result = health_agent.generate_medical_advice(profile, environment_data, survival_estimation)
        advice = result.get("medical_advice", "")
        assert "Identified risks include:" in advice
        assert "High risk due to critical health status." in advice


    def test_generate_medical_advice_immediate_evacuation(self, health_agent):
        profile = {"id": "patient3", "age": 30, "current_conditions": []}
        environment_data = {"temperature": 22, "pollution_level": 50}
        survival_estimation = {"estimated_survival_hours": 20}
        result = health_agent.generate_medical_advice(profile, environment_data, survival_estimation)
        advice = result.get("medical_advice", "")
        assert "Immediate evacuation is strongly recommended." in advice


    ### Tests for process_request

    def test_process_request_assemble_profile(self, health_agent):
        message = {
            "assemble_profile": True,
            "patient_data": {
                "id": "patient123",
                "age": 45,
                "medical_history": ["hypertension"],
                "allergies": ["penicillin"],
                "current_conditions": ["asthma"],
                "medications": [{"name": "DrugA", "dosage": "50mg", "frequency": "daily"}]
            }
        }
        result = health_agent.process_request(message)
        assert "profile" in result
        assert "message" in result


    def test_process_request_unknown(self, health_agent):
        message = {"invalid_request": True}
        result = health_agent.process_request(message)
        assert "error" in result
        assert result["error"] == "Unknown request type"


    def test_process_request_extrapolate_status(self, health_agent):
        message = {
            "extrapolate_status": True,
            "profile": {"id": "patient123", "age": 40, "current_conditions": ["asthma"]}
        }
        result = health_agent.process_request(message)
        assert "current_status" in result
        assert "health_score" in result


    def test_get_interactions_slug_success(self, health_agent):
        with patch.object(health_agent, 'get_interactions_slug', return_value='omaveloxolone,skyclarys'):
            assert health_agent.get_interactions_slug('skyclarys') == 'omaveloxolone,skyclarys'

    def test_get_interactions_slug_failure(self, health_agent):
        with patch.object(health_agent, 'get_interactions_slug', side_effect=Exception("Drug not found")):
            with pytest.raises(Exception, match="Drug not found"):
                health_agent.get_interactions_slug('unknown_drug')

    def test_get_interactions_slug_empty(self, health_agent):
        with patch.object(health_agent, 'get_interactions_slug', return_value=''):
            assert health_agent.get_interactions_slug('') == ''

    def test_get_drug_interactions_success(self, health_agent):
        mock_data = {'major': ['Aspirin'], 'moderate': ['Ibuprofen']}
        with patch.object(health_agent, 'get_drug_interactions', return_value=mock_data):
            assert health_agent.get_drug_interactions('omaveloxolone,skyclarys') == mock_data

    def test_get_drug_interactions_empty(self, health_agent):
        with patch.object(health_agent, 'get_drug_interactions', return_value={'major': [], 'moderate': []}):
            assert health_agent.get_drug_interactions('omaveloxolone,skyclarys') == {'major': [], 'moderate': []}

    def test_get_drug_interactions_failure(self, health_agent):
        with patch.object(health_agent, 'get_drug_interactions', side_effect=Exception("Invalid slug")):
            with pytest.raises(Exception, match="Invalid slug"):
                health_agent.get_drug_interactions('invalid_slug')

    def test_get_food_interactions_text_success(self, health_agent):
        mock_text = "Avoid grapefruit while taking this drug."
        with patch.object(health_agent, 'get_food_interactions_text', return_value=mock_text):
            assert health_agent.get_food_interactions_text('omaveloxolone,skyclarys') == mock_text

    def test_get_food_interactions_text_empty(self, health_agent):
        with patch.object(health_agent, 'get_food_interactions_text', return_value=''):
            assert health_agent.get_food_interactions_text('omaveloxolone,skyclarys') == ''

    def test_get_food_interactions_text_failure(self, health_agent):
        with patch.object(health_agent, 'get_food_interactions_text', side_effect=Exception("Page not found")):
            with pytest.raises(Exception, match="Page not found"):
                health_agent.get_food_interactions_text('invalid_slug')

    def test_get_all_interactions_success(self, health_agent):
        mock_data = {
            "drug_name": "skyclarys",
            "slug": "omaveloxolone,skyclarys",
            "drug_interactions": {"major": ["Aspirin"], "moderate": ["Ibuprofen"]},
            "food_interactions": "Avoid grapefruit.",
            "disease_interactions": "Use with caution in liver disease."
        }
        with patch.object(health_agent, 'get_all_interactions', return_value=mock_data):
            assert health_agent.get_all_interactions('skyclarys') == mock_data

    def test_get_all_interactions_empty(self, health_agent):
        with patch.object(health_agent, 'get_all_interactions', return_value={}):
            assert health_agent.get_all_interactions('skyclarys') == {}

    def test_get_all_interactions_failure(self, health_agent):
        with patch.object(health_agent, 'get_all_interactions', side_effect=Exception("Error fetching data")):
            with pytest.raises(Exception, match="Error fetching data"):
                health_agent.get_all_interactions('skyclarys')


    ### Tests for update_status and get_status

    def test_update_get_status_initial(self, health_agent):
        assert health_agent.get_status() == "standby"


    def test_update_get_status_update(self, health_agent):
        health_agent.update_status("in_progress")
        assert health_agent.get_status() == "in_progress"


    def test_update_get_status_multiple(self, health_agent):
        health_agent.update_status("phase_1")
        health_agent.update_status("phase_2")
        assert health_agent.get_status() == "phase_2"
