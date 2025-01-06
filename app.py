import pandas as pd
import openai
import time
import os
from flask import Flask, request, render_template

# Initialize Flask app
app = Flask(__name__)

# Retrieve the OpenAI API key from the environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Check if the API key is loaded properly
if not openai.api_key:
    print("API key is missing. Please ensure it's set in the environment.")
else:
    print("API key loaded successfully.")


# Function to handle CSV file
def process_csv(file_path):
    """Reads a CSV file and returns its contents as a pandas DataFrame."""
    try:
        data = pd.read_csv(file_path)
        return data
    except Exception as e:
        return f"Error reading CSV: {e}"


# Function to generate Python code from OpenAI API
def generate_code(user_message, csv_head):
    """Generates Python code based on the user message and CSV sample."""
    retries = 3
    for i in range(retries):
        try:
            # Define the prompt for the AI to generate Python code
            prompt = f"User request: {user_message}\nCSV sample:\n{csv_head}\nWrite Python code to process this."

            # Make API call to OpenAI's ChatGPT model
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # You can change to "gpt-4" if available and preferred
                messages=[{"role": "system", "content": "You are a helpful assistant generating Python code."},
                          {"role": "user", "content": prompt}]
            )

            # Log the response for debugging
            print(f"API Response: {response}")
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
    """Safely executes the generated Python code."""
    try:
        if "Error generating code" in code:
            raise ValueError("Invalid code generated. Cannot execute.")

        # Define a restricted global environment to execute the code
        exec_globals = {'pd': pd, '__builtins__': {}}

        # Execute the generated code
        exec(code, exec_globals)

        # Retrieve and return the result
        result = exec_globals.get('result', "No result returned.")
        return result
    except Exception as e:
        return f"Error executing code: {e}"


# Flask route to upload CSV and enter message
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['csv_file']
        user_message = request.form['message']

        if file:
            # Save uploaded CSV file temporarily
            file_path = f"uploaded_{file.filename}"
            file.save(file_path)

            # Step 1: Read CSV
            csv_data = process_csv(file_path)
            if isinstance(csv_data, str):
                return render_template('index.html', error=csv_data)
            else:
                # Prepare the CSV header for code generation
                csv_head = csv_data.head().to_string()

                # Step 2: Generate Python code using OpenAI
                generated_code = generate_code(user_message, csv_head)
                if "Error" in generated_code:
                    return render_template('index.html', error=generated_code)
                else:
                    print("Generated Code:\n", generated_code)

                    # Step 3: Execute the generated Python code
                    result = execute_code(generated_code, file_path)
                    return render_template('result.html', result=result)

    return render_template('index.html')


# Flask route for showing results
@app.route('/result', methods=['GET'])
def result():
    return render_template('result.html')


if __name__ == "__main__":
    app.run(debug=True)

