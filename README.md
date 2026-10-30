<h1 align="center">AI-Powered Python Code Evaluator</h1>

<h2>Overview</h2>

<p>
An AI-powered Python code evaluation system that combines <b>AST-based code analysis</b>, <b>test-case evaluation</b>, <b>machine learning-based anomaly detection</b>, and <b> LLM-generated feedback </b> to help users understand and improve their Python code.
</p>

<p>
This project has been developed as a proof of concept, taking inspiration from the functionalities and vision of <strong>Cynbit Studio</strong>, with a focus on AI-powered Python code evaluation, analysis, and personalized learning feedback.
</p>

<h2>Tech Stack</h2>

| Category | Tools |
|---|---|
| **Language & Dev** | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white) ![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white) |
| **Data & ML** | ![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white) ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white) ![Isolation Forest](https://img.shields.io/badge/Isolation%20Forest-1F6FEB?style=for-the-badge) |
| **Notebooks & Viz** | ![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white) ![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge) ![Seaborn](https://img.shields.io/badge/Seaborn-4C72B0?style=for-the-badge) |
| **AI & LLM** | ![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge) ![Qwen](https://img.shields.io/badge/Qwen-615CED?style=for-the-badge) |
| **Dashboard** | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white) |
| **Analysis & Testing** | ![Python AST](https://img.shields.io/badge/Python%20AST-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white) ![Radon](https://img.shields.io/badge/Radon-4B5563?style=for-the-badge) |
| **Utilities** | ![Joblib](https://img.shields.io/badge/Joblib-2E8B57?style=for-the-badge) ![Requests](https://img.shields.io/badge/Requests-24292E?style=for-the-badge) ![TQDM](https://img.shields.io/badge/TQDM-FFC107?style=for-the-badge&logoColor=black) ![python-dotenv](https://img.shields.io/badge/python--dotenv-ECD53F?style=for-the-badge&logo=dotenv&logoColor=black) |


## Project Structure

```text
AI-Powered-Python-Code-Evaluator/
│
├── AI Opportunity Report.pdf
├── README.md
├── app.py
├── requirements.txt
│
├── leetcode-dataset/
│   ├── LICENSE
│   ├── README.md
│   ├── data/
│   │   └── solutions.csv
│   └── dataset-metadata.json
│
├── notebooks/
│   ├── code_evaluator.ipynb
│   ├── leetcode_exploration.ipynb
│   └── model_training.ipynb
│
├── pipeline/
│   ├── __init__.py
│   ├── ai_feedback.py
│   ├── code_analyzer.py
│   ├── data_loader.py
│   ├── dataloader.py
│   ├── main.py
│   ├── ml_detector.py
│   ├── sandbox_runner.py
│   └── test_runner.py
│
└── reports/
    ├── anomaly_detection_results.csv
    ├── code_evaluation_results.csv
    ├── isolation_forest_model.joblib
    ├── leetcode_features.csv
    └── qwen_code_feedback.txt
```
## Pipeline Architecture

```mermaid

flowchart TD
    A["Python Source Code"] --> B["AST Code Analyzer"]
    B --> C{"Syntax Valid?"}

    C -->|No| D["Syntax Error Report"]
    C -->|Yes| E["Structural Feature Extraction"]

    E --> F["Isolation Forest Detector"]
    E --> G["Test Case Runner"]

    F --> H["Anomaly Detection Result"]
    G --> I["Functional Evaluation Results"]

    H --> J["Evaluation Summary"]
    I --> J

    J --> K["Qwen AI Feedback via Groq"]
    K --> L["Code Explanation & Improvement Suggestions"]

    L --> M["Streamlit Dashboard"]
```
