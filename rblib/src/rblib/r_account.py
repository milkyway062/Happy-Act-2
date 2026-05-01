import requests
from enum import Enum
class httpType(Enum):
    """
    Enum representing supported HTTP request methods for Roblox API calls.

    Attributes:
        GET (int):
            Perform an HTTP GET request.
        POST (int):
            Perform an HTTP POST request.
        PUT (int):
            Perform an HTTP PUT request.
        PATCH (int):
            Perform an HTTP PATCH request.
        DELETE (int):
            Perform an HTTP DELETE request.
    """
    GET = 0
    POST = 1
    PUT = 2
    PATCH = 3
    DELETE = 4
class Status(Enum):
    """
    Enum representing Roblox user presence states.

    Attributes:
        Offline (int):
            The user is offline.
        Online (int):
            The user is online but not actively in-game.
        Active (int):
            The user is actively in an experience.
    """
    Offline = 0 
    Online = 1
    Active = 2
class Account():
    """
    Represent an authenticated Roblox account using a .ROBLOSECURITY cookie.

    Attributes:
        UserCookie (str):
            The Roblox authentication cookie used for API requests.
    """
    def __init__(self,cookie: str):
        """
        Initialize an Account instance with a Roblox security cookie.

        Args:
            cookie (str):
                A valid .ROBLOSECURITY cookie for the Roblox account.
        """
        self.UserCookie = cookie
    @property
    def userId(self) -> int:
        """
        Get the authenticated user's Roblox user ID.

        Returns:
            int | str:
                The authenticated user's ID if successful, otherwise an error string.

        Notes:
            This fetches the authenticated user info from the Roblox users API.
        """
        user_info = self._get_user_info()
        return user_info['id'] if user_info.get("id") is not None else user_info["Error"]
    @property
    def name(self) -> int:
        """
        Get the authenticated user's Roblox username.

        Returns:
            str:
                The account username if successful, otherwise an error string.

        Notes:
            This fetches the authenticated user info from the Roblox users API.
        """
        user_info = self._get_user_info()
        return user_info['name'] if user_info.get("id") is not None else user_info["Error"]
    @property
    def displayName(self) -> int:
        """
        Get the authenticated user's Roblox display name.

        Returns:
            str:
                The display name if successful, otherwise an error string.

        Notes:
            This fetches the authenticated user info from the Roblox users API.
        """
        user_info = self._get_user_info()
        return user_info['displayName'] if user_info.get("id") is not None else user_info["Error"]
    @property
    def status(self) -> Status:
        """
        Get the authenticated user's current Roblox presence status.

        Returns:
            Status | int:
                A Status enum value if successful, otherwise the HTTP status code.

        Notes:
            This sends a POST request to the Roblox presence API and converts
            userPresenceType into the Status enum.
        """
        userPresences = self.roblox_api_call(
            endpoint_url=" https://presence.roblox.com/v1/presence/users",
            body={"userIds": self.userId},
            hType=httpType.POST,
            requires_cookies=False
        )
        return Status(userPresences.json()["userPresences"][0]["userPresenceType"]) if userPresences.status_code == 200 else userPresences.status_code
    @property
    def description(self) -> Status:
        """
        Get the authenticated user's profile description.

        Returns:
            str | int:
                The account description if successful, otherwise the HTTP status code.

        Notes:
            This requests the description endpoint from the Roblox users API.
        """
        response = self.roblox_api_call(
            endpoint_url="https://users.roblox.com/v1/description",
            hType=httpType.GET,
        )
        return response.json()["description"] if response.status_code == 200 else response.status_code
    
    def _get_user_info(self) -> dict:
        """
        Fetch the authenticated user's account information from Roblox.

        Returns:
            dict:
                The JSON response containing user data if successful, otherwise
                a dictionary with an "Error" key.

        Notes:
            This calls the authenticated users endpoint and is used internally
            by the userId, name, and displayName properties.
        """
        r = self.roblox_api_call(
            endpoint_url="https://users.roblox.com/v1/users/authenticated",
            hType=httpType.GET
        )
        if r.status_code == 200:
            return r.json()
        return {"Error": f"Error getting user info: {r.status_code}"}

    def _generate_csrf(self) -> str:
        """
        Generate a CSRF token for authenticated Roblox web requests.

        Returns:
            str:
                The X-CSRF-TOKEN required for authenticated Roblox API requests.

        Notes:
            This sends a logout request to Roblox to force a CSRF token response.
        """
        r = self.roblox_api_call(
            endpoint_url="https://auth.roblox.com/v2/logout",
            hType=httpType.POST,
            requires_cookies=True,
            requires_csrf=False
        )
        csrf = r.headers.get("X-CSRF-TOKEN")
        return csrf or f"Error creating csrf : {r.status_code}"

    def _generate_ticket(self) -> str:
        """
        Generate a Roblox authentication ticket for launching an authenticated
        Roblox client session.

        Returns:
            str:
                The rbx-authentication-ticket used in Roblox launch protocol URLs.

        Notes:
            Requires a valid .ROBLOSECURITY cookie and a valid CSRF token.
        """
        r = self.roblox_api_call(
            endpoint_url="https://auth.roblox.com/v1/authentication-ticket",
            hType=httpType.POST,
            requires_cookies=True,
            requires_csrf=True,
            headers={                
                "Referer": "www.roblox.com", 
                "Content-Type": "application/json",
                "RBX-For-Gameauth": "true" 
            }
        )
        ticket = r.headers.get("rbx-authentication-ticket")
        return ticket or f"error creating ticket : {r.status_code}"

    def roblox_api_call(self,endpoint_url: str,hType:httpType,body: dict | None = None ,cookies: dict | None = None,headers: dict | None = None, requires_cookies=True,requires_csrf=False)->requests.Response:
        """
        Perform a Roblox API request with optional authentication and CSRF handling.

        Args:
            endpoint_url (str):
                The full Roblox API endpoint URL.
            hType (httpType):
                The HTTP method to use for the request.
            body (dict):
                Request body data to send with the request.
            cookies (dict):
                Additional cookies to include in the request.
            headers (dict):
                Additional headers to include in the request.
            requires_cookies (bool):
                Whether to automatically attach the account's .ROBLOSECURITY cookie.
            requires_csrf (bool):
                Whether to automatically generate and attach an X-CSRF-TOKEN header.

        Returns:
            requests.Response:
                The raw response object returned by the requests library.

        Notes:
            If requires_cookies is True, the account's .ROBLOSECURITY cookie is
            inserted into the request cookies.

            If requires_csrf is True, a CSRF token is generated and inserted into
            the request headers before sending the request.
        """
        body = body or {}
        cookies = cookies or {}
        headers = headers or {}
        if requires_cookies:
            cookies[".ROBLOSECURITY"] = self.UserCookie
        if requires_csrf:
            headers["X-CSRF-TOKEN"] = self._generate_csrf()
        match hType:
            case httpType.POST:
                return requests.post(url=endpoint_url,data=body,cookies=cookies,headers=headers)
            case httpType.GET:
                return requests.get(url=endpoint_url,data=body,cookies=cookies,headers=headers)
            case httpType.PUT:
                return requests.put(url=endpoint_url,data=body,cookies=cookies,headers=headers)
            case httpType.PATCH:
                return requests.patch(url=endpoint_url,data=body,cookies=cookies,headers=headers)
            case httpType.DELETE:
                return requests.delete(url=endpoint_url,data=body,cookies=cookies,headers=headers)
    

