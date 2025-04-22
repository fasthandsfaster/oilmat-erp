import subprocess
import os

def start_flask_app(workshop, erp_type, api_port=8001):
    # Define the path to the app.py script
    app_path = os.path.join(os.path.dirname(__file__), 'flask_api', 'app.py')
    
    # Command to start the Flask app
    command = [
        'python', app_path, workshop, erp_type, str(api_port)
    ]
    
    # Redirect output to a log file
    with open('flask_app.log', 'a') as log_file:
        subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT, close_fds=True)

    print(f"Flask app started in the background. Logs are being written to flask_app.log.")

# Example usage
if __name__ == '__main__':
    # Replace these with actual arguments
    workshop_name = 'example_workshop'
    erp_type = 'admanager'
    port = 8001

    start_flask_app(workshop_name, erp_type, port)