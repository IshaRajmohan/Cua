import argparse
import json
import os
from computers.local_playwright import LocalPlaywrightComputer
from agent.agent import Agent
from testing.test_utils import TestResults, create_test_instructions

def run_test(url, test_file, headless=False, show_images=False, debug=False):
    """
    Run a test against a website using the OpenAI CUA
    
    Args:
        url: The URL of the website to test
        test_file: Path to test file (JSON)
        headless: Whether to run the browser in headless mode
        show_images: Whether to display images during test
        debug: Whether to enable debug output
    """
    
    with open(test_file, 'r') as f:
        test_data = json.load(f)
    
    test_name = test_data.get('name', 'Unnamed Test')
    test_steps = test_data.get('steps', [])
    
    
    results = TestResults(test_name)

    
    instructions = create_test_instructions(url, test_steps)
    
    # Set up the computer and agent
    with LocalPlaywrightComputer(headless=headless) as computer:
        
        computer.goto(url)
        
        agent = Agent(computer=computer)
        

        screenshot = computer.screenshot()
        results.add_step("Initial page load", "Info", screenshot)
        
        
        print(f"Running test: {test_name}")
        print(f"Testing URL: {url}")
        
        try:
            # Set up the initial system message
            conversation = [
                {"role": "system", "content": instructions}
            ]
            
            for i, step in enumerate(test_steps, 1):
                print(f"\nExecuting Step {i}: {step['description']}")
                
                # Add user prompt for this step
                step_prompt = f"Execute test step {i}: {step['description']}\nExpected outcome: {step['expected']}"
                
                # Create input items for this turn
                input_items = conversation + [{"role": "user", "content": step_prompt}]
                
                # Run the agent for one turn
                output_items = agent.run_full_turn(
                    input_items=input_items,
                    print_steps=True,
                    debug=debug,
                    show_images=show_images
                )
                
                # Find the assistant's response in the output items
                assistant_response = next((item["content"][0]["text"] 
                                         for item in output_items 
                                         if item.get("type") == "message" and item.get("role") == "assistant"), 
                                         "No response from assistant")
            
                
                screenshot = computer.screenshot()
                
                # Determine status based on response content
                status = "Pass" if "PASS" in assistant_response.upper() else "Fail" if "FAIL" in assistant_response.upper() else "Unknown"
                
                # Record step result
                results.add_step(step['description'], status, screenshot)
                
                # Update conversation for next turn
                conversation.append({"role": "user", "content": step_prompt})
                for item in output_items:
                    if item.get("role") in ["assistant", "system"]:
                        conversation.append(item)
                
            
            overall_status = "Pass" if all(s["status"] == "Pass" for s in results.steps if s["status"] != "Info") else "Fail"
            results.complete(overall_status)
            
            print(f"\nTest completed with status: {overall_status}")
            print(f"Test report available at: {results.report_dir}/report.html")
            
        except Exception as e:
            print(f"Error during test execution: {str(e)}")
            results.add_step(f"Error: {str(e)}", "Fail")
            results.complete("Error")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run automated web tests using OpenAI CUA")
    parser.add_argument("--url", required=True, help="URL to test")
    parser.add_argument("--test", required=True, help="Path to test file (JSON)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--show-images", action="store_true", help="Show images during test")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    run_test(args.url, args.test, args.headless, args.show_images, args.debug)