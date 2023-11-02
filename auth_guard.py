from fastapi import HTTPException
import re
from supabase import Client
from config import SUPABASE_URL, SUPABASE_URL_API_KEY

# Initialize Supabase client
supabase = Client(SUPABASE_URL, SUPABASE_URL_API_KEY)

# Function to validate the user's authentication token and extract user information
async def auth_guard(token: str):
    # Check if the token is provided, if not, raise an Unauthorized HTTPException
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # Remove "Bearer" from the token and decode the token using Firebase Admin's verify_id_token method
        auth_token = remove_bearer(token)
        decoded_token=supabase.auth.get_user(auth_token) 
        
        return decoded_token
    
    except Exception as e:
        # If there is any other error while validating the token, raise an HTTPException with status code 401
        raise HTTPException(status_code=403, detail="Failed to Authorize")
# Function to remove the "Bearer" keyword from the Authorization token
def remove_bearer(token):
    """Remove Bearer from Authorization token"""
    # Use a regular expression to match the "Bearer" keyword and extract the actual token
    match = re.search(r"^Bearer (.*)$", token)
    if match:
        return match.group(1)
    else:
        # If "Bearer" is not found, return the token as it is
        return token
