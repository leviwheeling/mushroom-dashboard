# Instructions for Setting Up and Using the Mushroom Farm AI Assistant (v2 - Gemma3)

This guide will walk you through setting up the custom AI model for your mushroom farm. This model, `mushroom_gemma`, is built using Ollama and the `gemma3:12b` base model.

## 1. Install or Update Ollama

First, you need to ensure you have Ollama version 0.6 or later installed on your operating system. The `gemma3` models require a recent version of Ollama.
- Go to the official Ollama download page: [https://ollama.com/download](https://ollama.com/download)
- Download the appropriate version for your system (Windows, macOS, or Linux) and follow the installation instructions. If you have an older version of Ollama, please update it.

## 2. Save the Modelfile

You will need the Modelfile that defines our custom `mushroom_gemma` model. The content of this file is:

```Modelfile
FROM gemma3:12b

SYSTEM """You are a helpful AI assistant for a mushroom farm.
You will receive sensor data (e.g., temperature, humidity, CO2 levels) and user questions.
Sometimes, questions will be augmented with relevant documents or historical data from our farm's operations, possibly retrieved from a vector database (RAG).
Your responses should be concise, informative, and tailored to the specific mushroom growing zone the user is asking about.
You are capable of processing both text and images, though for this project, the primary interaction will be text-based. If image data is ever provided (e.g., a picture of a mushroom bed with a potential issue), you can incorporate that information into your analysis and response.
Focus on providing actionable advice or clear explanations based on all information provided.
If sensor data indicates an issue, suggest potential causes and remedies relevant to mushroom cultivation.
If asked about past data or documents, summarize the key relevant points for the current query.
Always maintain a helpful and professional tone.
"""

PARAMETER temperature 0.7
PARAMETER top_k 64
```

- Create a new file named `gemma_mushroom_modelfile` in your project directory.
- Copy and paste the entire content above into this `gemma_mushroom_modelfile` file.
- Save the file.

*(Note: If you are updating from a previous version, this will overwrite your old `gemma_mushroom_modelfile` if you use the same name. You might want to back up the old one if needed.)*

## 3. Pull the Base Model

Before creating the custom model, you need to download the base model `gemma3:12b` from Ollama.
- Open your terminal or command prompt.
- Run the following command:
  ```bash
  ollama pull gemma3:12b
  ```
- This model is larger than `gemma:7b` and might take a significant amount of time to download, depending on your internet connection.

## 4. Create the Custom Model

Once the base model is downloaded and the `gemma_mushroom_modelfile` is in place, you can create the custom model.
- In your terminal, navigate to the directory where you saved `gemma_mushroom_modelfile`.
- Run the following command:
  ```bash
  ollama create mushroom_gemma -f gemma_mushroom_modelfile
  ```
- Ollama will process the Modelfile and create the `mushroom_gemma` model. You should see output indicating the model is being created. If you had an older `mushroom_gemma` model, this command will update it.

## 5. Verify Model Creation

To ensure your custom model `mushroom_gemma` has been created or updated successfully:
- Run the following command in your terminal:
  ```bash
  ollama list
  ```
- You should see `mushroom_gemma` listed among your available Ollama models. Check its name and that it's associated with `gemma3:12b` (Ollama might show the base model family or a digest).

You are now ready to use the updated `mushroom_gemma` model with Ollama!
For example, you can interact with it using `ollama run mushroom_gemma`.
If you have applications using this model, ensure they are configured to use the correct model name if you've made any changes.
