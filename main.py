from fastmcp import FastMCP
import random
import json


# cretae the fastmcp server instance
mcp = FastMCP("Simple calculator server")


# tool: add two number
@mcp.tool
def add(a: int, b: int) -> int:
    """add two numbers together,


    Args:
        a:First number
        b:second number

    Return:
        the sum of a and b
    """
    return a + b


# tool: Generate a random number
@mcp.tool
def random_number(min_val: int = 1, max_val: int = 100) -> int:
    """generate a random number within a range.

    args:
        min_val: minimum value (default:1)
        max_val: maximum value (default:100)

    return:
        A random integer between min_val and max_val"""

    return random.randint(min_val, max_val)


# resources server information
@mcp.resource("info://server")
def server_info() -> str:
    """get information about this server"""

    info = {
        "name": "simple calculator server",
        "version": "1.0.0",
        "description": "A basic mcp server with math tools",
        "tools": ["add", "random_number"],
        "author": "harsha",
    }
    return json.dumps(info, indent=2)


# start the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
