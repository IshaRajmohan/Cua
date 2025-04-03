import os
import json
import base64
from datetime import datetime
from PIL import Image
import io

class TestResults:
    def __init__(self, test_name):
        self.test_name = test_name
        self.start_time = datetime.now()
        self.steps = []
        self.status = "Running"
        self.report_dir = os.path.join("testing", "reports", test_name.replace(" ", "_"))
        os.makedirs(self.report_dir, exist_ok=True)
    
    def add_step(self, description, status, screenshot=None):
        step_num = len(self.steps) + 1
        step_data = {
            "step": step_num,
            "description": description,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if screenshot:
            screenshot_path = os.path.join(self.report_dir, f"step_{step_num}.png")
            # Save screenshot if it's base64 encoded
            if isinstance(screenshot, str) and screenshot.startswith("data:image"):
                img_data = screenshot.split(",")[1]
                with open(screenshot_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                step_data["screenshot"] = screenshot_path
        
        self.steps.append(step_data)
        return step_num
    
    def complete(self, status):
        self.status = status
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        
        # Save test results as JSON
        results = {
            "test_name": self.test_name,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration,
            "steps": self.steps
        }
        
        with open(os.path.join(self.report_dir, "results.json"), "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate a simple HTML report
        self._generate_html_report()
        
        return results
    
    def _generate_html_report(self):
        """Generate a simple HTML report from the test results"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report: {self.test_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 10px; }}
                .step {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
                .pass {{ background-color: #dff0d8; }}
                .fail {{ background-color: #f2dede; }}
                .running {{ background-color: #d9edf7; }}
                img {{ max-width: 100%; border: 1px solid #ddd; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Report: {self.test_name}</h1>
                <p>Status: <strong>{self.status}</strong></p>
                <p>Duration: {self.duration:.2f} seconds</p>
                <p>Start Time: {self.start_time.isoformat()}</p>
                <p>End Time: {self.end_time.isoformat()}</p>
            </div>
            
            <h2>Test Steps:</h2>
        """
        
        for step in self.steps:
            status_class = "pass" if step["status"] == "Pass" else "fail" if step["status"] == "Fail" else "running"
            html += f"""
            <div class="step {status_class}">
                <h3>Step {step["step"]}: {step["description"]}</h3>
                <p>Status: <strong>{step["status"]}</strong></p>
                <p>Time: {step["timestamp"]}</p>
            """
            
            if "screenshot" in step:
                screenshot_path = os.path.basename(step["screenshot"])
                html += f'<img src="{screenshot_path}" alt="Step {step["step"]} Screenshot">'
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        with open(os.path.join(self.report_dir, "report.html"), "w") as f:
            f.write(html)


def create_test_instructions(website_url, test_steps):
    """
    Create instructions for the agent to test a website
    
    Args:
        website_url: The URL of the website to test
        test_steps: A list of test steps with descriptions and expected outcomes
        
    Returns:
        A formatted instruction string for the agent
    """
    instructions = f"""
You are a website testing agent. Your task is to test the website at {website_url}.

Follow these test steps carefully and report your findings:

"""
    
    for i, step in enumerate(test_steps, 1):
        instructions += f"""
Step {i}: {step['description']}
Expected outcome: {step['expected']}

"""
    
    instructions += """
For each step:
1. Describe what you are doing
2. Take a screenshot
3. Report if the step passed or failed based on the expected outcome
4. If it failed, explain why

Be thorough, accurate, and report any unexpected behavior.
"""
    
    return instructions