import pandas as pd
import openai
import time
import os

# Retrieve the OpenAI API key from the environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Check if the API key is loaded properly
if not openai.api_key:
    print("API key is missing. Please ensure it's set in the environment.")
else:
    print("API key loaded successfully.")

# Function to handle CSV file
def process_csv(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except Exception as e:
        return f"Error reading CSV: {e}"

# Function to generate Python code from OpenAI API
# Function to generate Python code from OpenAI API
def generate_code(user_message, csv_head):
    retries = 3
    for i in range(retries):
        try:
            prompt = f"User request: {user_message}\nCSV sample:\n{csv_head}\nWrite Python code to process this."

            # Make API call
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful assistant generating Python code."},
                          {"role": "user", "content": prompt}]
            )

            print(f"API Response: {response}")  # Log the response for debugging
            return response['choices'][0]['message']['content'].strip()

        except openai.error.RateLimitError:
            print(f"Rate limit reached. Retrying in 5 seconds... (Attempt {i + 1}/{retries})")
            time.sleep(5)
        except openai.error.OpenAIError as e:
            print(f"API error: {e}")
            return f"Error generating code: {e}"

    return "Failed to generate code after multiple retries."

# Function to execute generated Python code
def execute_code(code, file_path):
    try:
        if "Error generating code" in code:
            raise ValueError("Invalid code generated. Cannot execute.")

        exec_globals = {'pd': pd, '__builtins__': {}}
        exec(code, exec_globals)
        result = exec_globals.get('result', "No result returned.")
        return result
    except Exception as e:
        return f"Error executing code: {e}"

# Main flow
if __name__ == "__main__":
    csv_path = 'input.csv'
    user_message = "Calculate the average salary of employees."  # Example input

    # Step 1: Read CSV
    csv_data = process_csv(csv_path)
    if isinstance(csv_data, str):
        print(csv_data)
    else:
        csv_head = csv_data.head().to_string()

        # Step 2: Generate Code
        generated_code = generate_code(user_message, csv_head)
        print("Generated Code:\n", generated_code)

        # Step 3: Execute Code
        result = execute_code(generated_code, csv_path)
        print("Execution Response:\n", result)
