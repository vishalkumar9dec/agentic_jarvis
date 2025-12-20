"""
Authenticated Toolbox Client
Wraps ToolboxSyncClient to add JWT authentication headers to tool invocations.
"""

from typing import Optional, Dict, Any, List
from toolbox_core import ToolboxSyncClient
import requests


class AuthenticatedToolboxClient:
    """
    Wrapper around ToolboxSyncClient that adds JWT authentication to tool calls.

    This client automatically includes the Bearer token in all tool invocation requests,
    allowing authenticated tools to access user-specific data.
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Initialize authenticated toolbox client.

        Args:
            base_url: Base URL of the toolbox server (e.g., http://localhost:5001)
            token: JWT token for authentication (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self._toolbox_client = ToolboxSyncClient(base_url)

    def set_token(self, token: str):
        """Set or update the JWT token."""
        self.token = token

    def clear_token(self):
        """Clear the JWT token."""
        self.token = None

    def load_toolset(self, toolset_name: str) -> List[Any]:
        """
        Load toolset from the server.

        Args:
            toolset_name: Name of the toolset to load

        Returns:
            List of tools from the toolset
        """
        # Use the standard toolbox client for loading (no auth required)
        return self._toolbox_client.load_toolset(toolset_name)

    def invoke_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Invoke a tool with authentication.

        Args:
            tool_name: Name of the tool to invoke
            params: Parameters for the tool

        Returns:
            Tool execution result
        """
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        # Make authenticated request to tool endpoint
        url = f"{self.base_url}/api/tool/{tool_name}/invoke"

        try:
            response = requests.post(url, json=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('result')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise PermissionError(f"Authentication required for tool '{tool_name}'")
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to invoke tool '{tool_name}': {str(e)}")


def create_authenticated_toolbox(base_url: str, token: Optional[str] = None) -> AuthenticatedToolboxClient:
    """
    Factory function to create an authenticated toolbox client.

    Args:
        base_url: Base URL of the toolbox server
        token: Optional JWT token for authentication

    Returns:
        AuthenticatedToolboxClient instance
    """
    return AuthenticatedToolboxClient(base_url, token)
