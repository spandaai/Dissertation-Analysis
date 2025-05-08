# Langflow: Dissertation Analysis Setup Guide

This guide walks you through the steps to install Langflow, load the `Dissertation Analysis.json` flow, and run it with a dissertation PDF and a rubric JSON file.

---

## 📦 Prerequisites

Make sure you have the following installed:

- Python 3.8+
- Git (optional, if cloning Langflow repo)
- A modern web browser (e.g., Chrome, Firefox)

---

## 🔧 Installation

You can install Langflow using pip:

```bash
pip install langflow
```

Or, if you want to run the latest version from source:

```bash
git clone https://github.com/langflow-ai/langflow.git
cd langflow
pip install -e .
```

---

## 🚀 Starting Langflow

To launch the Langflow interface:

```bash
langflow run
```

This will start a local server (by default at http://localhost:7860) where you can interact with your flows.

---

## 📥 Loading the Flow

To load your custom flow:

1. Open your browser and navigate to `http://localhost:7860`.
2. Click the folder icon or **"Upload Flow"** button.
3. Select and upload the `Dissertation Analysis.json` file.

The flow will now appear in the canvas.

---

## 📝 Running the Flow

To evaluate a dissertation:

1. On the canvas, locate the input nodes expecting:
   - A **PDF file** input (your dissertation).
   - A **Rubric JSON** input (evaluation criteria).
2. Click on the **file upload areas** in those nodes and upload the appropriate files:
   - Dissertation: a `.pdf` file.
   - Rubric: a `.json` file.
3. Click **"Run"** or the play ▶️ icon at the top to execute the flow.

The flow will process the dissertation according to the rubric and output the results.

---

## 🧾 Notes

- Ensure your flow nodes are configured to accept `file` inputs for both PDF and JSON.
- If the flow uses custom Python code or tools, ensure all dependencies are installed.
- You can export results or modify the flow as needed to customize analysis.

---

## 🆘 Troubleshooting

- **Flow doesn't load:** Ensure your `Dissertation Analysis.json` file is valid. Re-import it to Langflow if needed.

---

Happy analyzing! 🎓
