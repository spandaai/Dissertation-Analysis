# Dissertation Analysis

INSERT FLOWCHART

## Overview

The **Dissertation Analysis System** is designed to evaluate and analyze dissertations submitted by graduate students. This system leverages advanced analytics to assess the quality, originality, and impact of dissertations, helping academic committees ensure high standards in research outputs. With integration into Apache Superset, the system provides insightful visualizations and metrics for comprehensive dissertation assessment.

---

## Features

- **Comprehensive Dissertation Evaluation**: Analyzes various aspects of dissertations, including structure, content quality, originality, and adherence to academic standards.
- **Plagiarism Detection**: Utilizes advanced algorithms to detect potential plagiarism, ensuring the integrity of research work.
- TO DO - **Apache Superset Analytics Integration**: Provides detailed visual analytics and dashboards through Apache Superset, enabling academic committees to track trends, identify common strengths and weaknesses, and make informed decisions.
- **Customizable Evaluation Criteria**: Allows for the definition of specific evaluation parameters based on departmental or institutional standards, ensuring a tailored assessment approach.
- **Automated Reporting**: Generates detailed reports summarizing the evaluation results, highlighting areas of excellence and suggesting improvements where necessary.
- **Data-Driven Insights**: Uses collected data to inform curriculum development and enhance the overall quality of research training programs.

---


## Prerequisites

Before running the project, make sure you have the following installed:

- [Verba](https://github.com/spandaai/Verba-2.0)
- Python 3.10 (for backend services)
- Ollama and the required generation model chosen

---

## Steps to run the app

### How to build from Source

1. **Clone the Dissertation-Analysis repo**

2. **Create and Initialize a new Python Environment**

For linux/macOS
```
python3 -m virtualenv venv
source venv/bin/activate
```
For Windows
```
python -m virtualenv venv
venv/scripts/activate
```

3. **Install Dissertation-Analysis and its dependencies**

```
pip install -r requirements.txt
pip install -e .
```

4. **Launch Dissertation-Analysis**

```
da-start
```

> You can specify the --port and --host via flags

---

## Contributing

Add contribution steps

---

## License

Add license details

---
