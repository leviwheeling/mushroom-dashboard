# Instructions for Setting Up and Using the Mushroom Farm AI Assistant

This guide will walk you through setting up the custom AI model for your mushroom farm. This model, `mushroom_gemma`, is built using Ollama and the `gemma:7b` base model.

## 1. Install Ollama

First, you need to install Ollama on your operating system.
- Go to the official Ollama download page: [https://ollama.com/download](https://ollama.com/download)
- Download the appropriate version for your system (Windows, macOS, or Linux) and follow the installation instructions provided on the website.

## 2. Save the Modelfile

You will need the Modelfile that defines our custom `mushroom_gemma` model. The content of this file is:

```Modelfile
FROM gemma:7b

SYSTEM """You are a helpful AI assistant for a mushroom farm.
You will receive sensor data (e.g., temperature, humidity, CO2 levels) and user questions.
Sometimes, questions will be augmented with relevant documents or historical data from our farm's operations, possibly retrieved from a vector database (RAG).
Your responses should be concise, informative, and tailored to the specific mushroom growing zone the user is asking about.
Focus on providing actionable advice or clear explanations based on the information provided.
If sensor data indicates an issue, suggest potential causes and remedies relevant to mushroom cultivation.
If asked about past data or documents, summarize the key relevant points for the current query.
Always maintain a helpful and professional tone.
"""

PARAMETER temperature 0.7
PARAMETER top_k 50
```

- Create a new file named `gemma_mushroom_modelfile` in your project directory.
- Copy and paste the entire content above into this `gemma_mushroom_modelfile` file.
- Save the file.

*(Alternatively, if the Modelfile has been provided to you as a separate file, ensure it is named `gemma_mushroom_modelfile` and located in your main project directory.)*

## 3. Pull the Base Model

Before creating the custom model, you need to download the base model `gemma:7b` from Ollama.
- Open your terminal or command prompt.
- Run the following command:
  ```bash
  ollama pull gemma:7b
  ```
- This might take some time, depending on your internet connection, as the model is several gigabytes in size.

## 4. Create the Custom Model

Once the base model is downloaded and the `gemma_mushroom_modelfile` is in place, you can create the custom model.
- In your terminal, navigate to the directory where you saved `gemma_mushroom_modelfile`.
- Run the following command:
  ```bash
  ollama create mushroom_gemma -f gemma_mushroom_modelfile
  ```
- Ollama will process the Modelfile and create the `mushroom_gemma` model. You should see output indicating the model is being created.

## 5. Verify Model Creation

To ensure your custom model `mushroom_gemma` has been created successfully:
- Run the following command in your terminal:
  ```bash
  ollama list
  ```
- You should see `mushroom_gemma` listed among your available Ollama models, along with its size and when it was last modified.

You are now ready to use the `mushroom_gemma` model with Ollama!
For example, you can interact with it using `ollama run mushroom_gemma`.
