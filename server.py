"""
LLM-Hackathon 2025

This is a tailored version that doesn't rely on ivoryos client,
less convoluted, easier to debug and work with)

"""
# ivoryos_mcp_server.py
import os
from typing import Optional, Dict, List, Any

from mcp.server.fastmcp import FastMCP
import httpx
from dotenv import load_dotenv


# Configuration - Modify these defaults for your setup
load_dotenv()
mcp = FastMCP("IvoryOS MCP")

# Global HTTP client and configuration
client = httpx.Client(follow_redirects=True)
url = os.getenv("IVORYOS_URL", "http://127.0.0.1:8000/ivoryos").rstrip('/')
login_data = {
    "username": os.getenv("IVORYOS_USERNAME", "admin"),
    "password": os.getenv("IVORYOS_PASSWORD", "admin")
}


def _check_authentication() -> None:
    """Check and handle authentication"""
    try:
        resp = client.get(f"{url}/", follow_redirects=False)
        if resp.status_code == httpx.codes.OK:
            return

        login_resp = client.post(f"{url}/auth/login", data=login_data)
        if login_resp.status_code != 200:
            raise Exception(f"Login failed with status {login_resp.status_code}")
    except httpx.ConnectError as e:
        raise Exception(f"Connection error during authentication: {e}") from e


# Direct MCP tool implementations
@mcp.tool("platform-info")
def get_platform_info() -> str:
    """Get platform information and available functions"""
    try:
        _check_authentication()
        snapshot = client.get(f"{url}/instruments").json()
        return (
            "workflow execution has 3 blocks, prep, main (iterate) and cleanup.\n"
            "one can execute the workflow using one of the 3 options:\n"
            "1. simple repeat for static workflow with `run_workflow_repeat`\n"
            "2. repeat with kwargs `run_workflow_kwargs`\n"
            "3. campaign `run_workflow_campaign`\n"
            f"Available functions: {snapshot}"
        )
    except Exception as e:
        return f"Error getting platform info: {str(e)}"


@mcp.tool("execution-status")
def get_execution_status():
    """Get workflow execution status"""
    try:
        _check_authentication()
        resp = client.get(f"{url}/executions/status")
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to get execution status: {resp.status_code}"
    except Exception as e:
        return f"Error getting workflow status: {str(e)}"


@mcp.tool("execute-task")
def execute_task(component: str, method: str, kwargs: Optional[Dict[str, Any]] = None):
    """Execute a robot task"""
    try:
        _check_authentication()
        if kwargs is None:
            kwargs = {}

        snapshot = client.get(f"{url}/instruments").json()

        if component not in snapshot:
            return f"Component {component} does not exist. Available: {list(snapshot.keys())}"

        kwargs["hidden_name"] = method
        kwargs["hidden_wait"] = False

        resp = client.post(f"{url}/instruments/{component}", json=kwargs)
        if resp.status_code == httpx.codes.OK:
            result = resp.json()
            return f"{result}. Use `get-execution-status` to monitor."
        else:
            return f"Failed to execute task: {resp.status_code}"
    except Exception as e:
        return f"Error executing task: {str(e)}"


@mcp.tool("list-workflow-scripts")
def list_workflow_scripts(search_key: str = '', deck_name: str = ''):
    """List workflow scripts"""
    try:
        _check_authentication()
        params = {}
        if deck_name:
            params['deck'] = deck_name
        if search_key:
            params['keyword'] = search_key
        resp = client.get(
            f"{url}/library/{deck_name}",
            params=params
        )
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to list workflow scripts: {resp.status_code}"
    except Exception as e:
        return f"Error listing workflow scripts: {str(e)}"


@mcp.tool("load-workflow-script")
def load_workflow_script(workflow_name: str):
    """Load a workflow script"""
    try:
        _check_authentication()
        resp = client.get(f"{url}/library/{workflow_name}")
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to load workflow script: {resp.status_code}"
    except Exception as e:
        return f"Error loading workflow script: {str(e)}"


@mcp.tool("submit-workflow-script")
def submit_workflow_script(workflow_name: str, main_script: str = "",
                           cleanup_script: str = "", prep_script: str = ""):
    """Submit a workflow script"""
    try:
        _check_authentication()
        resp = client.post(
            url=f"{url}/draft/submit_python",
            json={
                "workflow_name": workflow_name,
                "script": main_script,
                "cleanup": cleanup_script,
                "prep": prep_script
            }
        )
        if resp.status_code == httpx.codes.OK:
            return "Workflow script submitted successfully"
        else:
            return f"Failed to submit workflow script: {resp.status_code}"
    except Exception as e:
        return f"Error submitting workflow script: {str(e)}"


@mcp.tool("pause-and-resume")
def pause_and_resume():
    """Toggle pause and resume for workflow execution"""
    try:
        _check_authentication()
        resp = client.post(f"{url}/executions/pause-resume")
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to toggle pause/resume: {resp.status_code}"
    except Exception as e:
        return f"Error toggling workflow pause/resume: {str(e)}"


@mcp.tool("abort-pending-workflow")
def abort_pending_workflow():
    """Abort pending workflow execution"""
    try:
        _check_authentication()
        resp = client.post(f"{url}/executions/abort/next-iteration")
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to abort pending workflow: {resp.status_code}"
    except Exception as e:
        return f"Error aborting pending workflow: {str(e)}"


@mcp.tool("stop-current-workflow")
def stop_current_workflow():
    """Stop workflow execution after the current step"""
    try:
        _check_authentication()
        resp = client.post(f"{url}/executions/abort/next-task")
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to stop current workflow: {resp.status_code}"
    except Exception as e:
        return f"Error stopping current workflow: {str(e)}"


@mcp.tool("run-workflow-repeat")
def run_workflow_repeat(repeat_time: Optional[int] = None):
    """Run the loaded workflow with repeat times"""
    try:
        _check_authentication()
        resp = client.post(
            f"{url}/executions/config",
            json={"repeat": repeat_time if repeat_time is not None else None}
        )
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to start workflow execution: {resp.status_code}"
    except Exception as e:
        return f"Error starting workflow execution: {str(e)}"


@mcp.tool("run-workflow-kwargs")
def run_workflow_kwargs(kwargs_list: Optional[List[Dict[str, Any]]] = None):
    """Run the loaded workflow with a list of keyword arguments"""
    try:
        _check_authentication()
        resp = client.post(
            f"{url}/executions/config",
            json={"kwargs": kwargs_list}
        )
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to start workflow execution: {resp.status_code}"
    except Exception as e:
        return f"Error starting workflow execution: {str(e)}"


@mcp.tool("run-workflow-campaign")
def run_workflow_campaign(parameters: List[Dict[str, Any]],
                          objectives: List[Dict[str, Any]],
                          repeat: int = 25,
                          parameter_constraints: Optional[List[str]] = None):
    """Run the loaded workflow with ax-platform (credit: Honegumi)"""
    try:
        _check_authentication()
        if parameter_constraints is None:
            parameter_constraints = []

        resp = client.post(
            f"{url}/executions/config",
            json={
                "parameters": parameters,
                "objectives": objectives,
                "parameter_constraints": parameter_constraints,
                "repeat": repeat,
            }
        )
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to start workflow campaign: {resp.status_code}"
    except Exception as e:
        return f"Error starting workflow campaign: {str(e)}"


@mcp.tool("list-workflow-data")
def list_workflow_data(workflow_name: str = ""):
    """List workflow data"""
    try:
        _check_authentication()
        resp = client.get(
            f"{url}/executions/records",
            params={"keyword": workflow_name}
        )
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to list workflow data: {resp.status_code}"
    except Exception as e:
        return f"Error listing workflow data: {str(e)}"


@mcp.tool("load-workflow-data")
def load_workflow_data(workflow_id: int):
    """Load workflow data"""
    try:
        _check_authentication()
        resp = client.get(f"{url}/executions/records/{workflow_id}")
        if resp.status_code == httpx.codes.OK:
            return resp.json()
        else:
            return f"Failed to load workflow data: {resp.status_code}"
    except Exception as e:
        return f"Error loading workflow data: {str(e)}"


# Prompts
@mcp.prompt("generate-workflow-script")
def generate_custom_script() -> str:
    """Prompt for writing a workflow script. No authentication required"""
    return """
    find the most appropriate function based on the task description
    ,and write them into a Python function without need to import the deck. 
    And write only needed return values as dict
    ```
    def workflow_static():
        if True:
            results = deck.sdl.analyze(**{'param_1': 1, 'param_2': 2})
        time.sleep(1.0)
        return {'results':results,}
    ```
    or
    ```
    def workflow_dynamic(param_1, param_2):
        if True:
            results = deck.sdl.analyze(**{'param_1': param_1, 'param_1': param_2})
        time.sleep(1.0)
        return {'results':results,}
    ```
    Another example of scripting using building blocks
    ```
    def workflow_using_building_block():
        results = blocks.general.analyze()
        time.sleep(1.0)
        return {'results':results,}
    ```
    Please only use these available action names.
    """


@mcp.prompt("campaign-design")
def ax_campaign_design() -> str:
    """Prompt for writing a workflow campaign. No authentication required (template credit: Honegumi)"""
    return """
    these are examples code of creating parameters, objectives and constraints
    parameters=[
        {"name": "x1", "type": "fixed", "value": 10.0},
        {"name": "x2", "type": "range", "bounds": [0.0, 10.0]},
        {
            "name": "c1",
            "type": "choice",
            "is_ordered": False,
            "values": ["A", "B", "C"],
        },
    ]
    objectives=[
        {"name": "obj_1", "minimize": True},
        {"name": "obj_2", "minimize": False},
    ]
    parameter_constraints=[
        "x1 + x2 <= 15.0",  # example of a sum constraint, which may be redundant/unintended if composition_constraint is also selected
        "x1 + x2 <= {total}",  # reparameterized compositional constraint, which is a type of sum constraint
        "x1 <= x2",  # example of an order constraint
        "1.0*x1 + 0.5*x2 <= 15.0",  # example of a linear constraint. Note the lack of space around the asterisks
    ],
    """


if __name__ == "__main__":
    mcp.run()
