

# rblib

`rblib` is a Python library designed for roblox apis, roblox client, detections, utilities, and similiar stuff.

## Features


* **Roblox API Helpers**

  * Generate CSRF tokens for authenticated web requests
  * Access user info and account data

* **Input Simulation**
  * Low level inputs
  * Perform mouse clicks and right-clicks
  * Automate in-game actions

* **Utilities**

  * Screen capture and image caching
  * Pixel Detections

## Installation

```bash
pip install rblib
```
## Usage

```python
from rblib import r_util, r_input, r_client, r_account

rbAccount = r_account.Account(cookie)
# Capture a pixel color
color = r_util.pixel(100, 200)

# Generate a CSRF token
csrf = rbAccount._generate_csrf()

# Simulate a click
r_input.Click(150, 300)
```

## Documentation

Each function in `rblib` includes detailed docstrings with parameters and return values for easy reference. Examples:

```python
def pixel(x: int, y: int, relative=True) -> tuple[int, int, int]:
    """
    Get the RGB color of a pixel within the Roblox window.

    Args:
        x (int): X-coordinate
        y (int): Y-coordinate
        relative (bool): Whether the coordinates are relative to the Roblox window

    Returns:
        tuple[int, int, int]: RGB color values
    """
```

## Contributing

Contributions are welcome! Feel free to:

* Report issues
* Suggest new features
* Submit pull requests

Please follow PEP8 guidelines and include proper docstrings.

## License

`rblib` is released under the MIT License.
