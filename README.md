# Search and Rescue (SAR) Agent Framework - CSC 581

## Contributions of this Fork
Added a HealthAgent class that does the following:
            1. Assembling a general health profile of the missing person using available records.
            2. Extrapolating current health status based on the assembled profile.
            3. Analyzing medication data to assess potential drug interactions and effects.
            4. Evaluating environmental impacts on the subject’s health.
            5. Estimating survival time under current conditions.
            6. Planning appropriate medical resources for rescue operations.
            7. Assessing health risks that may arise during SAR operations.
            8. Generating medical advice for SAR teams in the field.
            9. Providing information on drug, food, and disease interactions by scraping drugs.com.
            10. Updating and retrieving the current mission status.

Finally, the agent is capable of feeding all of the assembled information into an LLM from OpenAI.

## Prerequisites

- Python 3.8 or higher
- pyenv (recommended for Python version management)
- pip (for dependency management)

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sar-project
```

2. Set up Python environment:
```bash
# Using pyenv (recommended)
pyenv install 3.9.6  # or your preferred version
pyenv local 3.9.6

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

3. Install dependencies:
For pip users:
```bash
pip install -r requirements.txt
pip install -e .
```
or for conda users:
```bash
conda env create -f environment.yml
```

4. Configure environment variables:

#### OpenAI:
- Obtain required API keys:
  1. OpenAI API key: Sign up at https://platform.openai.com/signup
- Update your `.env` file with the following:
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    ```
#### Google Gemini:
- Obtain required API keys:
  1. ``` pip install google-generativeai ```
  2. ``` import google.generativeai as genai ```
  3. Google Gemini API Key: Obtain at https://aistudio.google.com/apikey
- Configure with the following:
  ```
  genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
  ```

Make sure to keep your `.env` file private and never commit it to version control.

## Project Structure

```
sar-project/
├── src/
│   └── sar_project/         # Main package directory
│       └── agents/          # Agent implementations
│       └── config/          # Configuration and settings
│       └── knowledge/       # Knowledge base implementations
├── tests/                   # Test directory
├── pyproject.toml           # Project metadata and build configuration
├── requirements.txt         # Project dependencies
└── .env                     # Environment configuration
```
