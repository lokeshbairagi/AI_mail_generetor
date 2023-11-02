# Import necessary libraries and modules                               
import json                                                                      
import openai
import uvicorn
from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from config import SUPABASE_URL, SUPABASE_URL_API_KEY

# Import configurations and guards from other files
from config import OPEN_AI_API, PORT
from . import auth_guard

from supabase import Client

# Initialize Supabase client
supabase = Client(SUPABASE_URL, SUPABASE_URL_API_KEY)


# Define data models for the FastAPI endpoints
class MailContent(BaseModel):
    mail_content: str

class MailFeedBack(BaseModel):
    content_id : str
    feedback: str
    is_liked: bool

# Create a FastAPI instance
app = FastAPI()

# Define a system role for the assistant
system_role = {  
    "role": "system",
    "content": """You are an assistant who only writes sales mails based on the user input. It has to be really professional, straightforward and customer-centric. The mails need to be impressive and very professional. Always give a subject line and signature in every reply. Do not give any other reply other than a mail.
    Make sure the mails are short, keep them under 100 words."""
}

# Set the OpenAI API key
openai.api_key = OPEN_AI_API

# Helper function to get the GPT message with system and user roles
def get_gpt_message(content: MailContent):
    messages = [system_role] 
    messages.append({"role": "user", "content": content["mail_content"]})
    return messages

# Root endpoint to return a simple greeting message
@app.get("/")
async def root():
    return {"message": "Hello World from mail server"}

# Endpoint to generate a mail using GPT-3.5 based on user input
@app.post("/generate-mail")
async def answer_gpt3_5(request: Request):
    decoded_token =await auth_guard(request.headers.get("Authorization"))
    user_uid = decoded_token.user.id
    
    # Reference the 'mailAI' table in Supabase
    table = "mailAI"
    
    body: MailContent = await request.json()
    try:
        # Generate GPT-3.5 response using OpenAI API
        messages = get_gpt_message(body)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        #extracting assistance reply
        content = response.choices[0]['message']['content']
        
        # Insert generated mail and request data into Supabase
        insert_data = {"req": messages[1]['content'], "res": content, "user_uid" : user_uid}
        supabase_insert = supabase.table('mailAI').insert(insert_data)
        db_res = supabase_insert.execute()
        
        # Return the generated content and response status
        return {"content": content, "error_status": False, "content_id": json.loads(db_res.json())['data'][0]['id'], "message": "Mail generated successfully"}
    except Exception as e:
        
        return {"error_status": True, "message": "Error in generating mail"}

# Endpoint to get message history based on user's JWT token, with limit and range
@app.get("/message-history")
async def get_message_history(
    request: Request,
    limit: int = Query(default=10, description="Number of records to fetch"),
    start: int = Query(default=0, description="Starting index for range")
):
    decoded_token = await auth_guard(request.headers.get("Authorization"))
    user_uid = decoded_token["uid"]
    
    # Reference the 'mailAI' table in Supabase
    table = "mailAI"
    
    # Query the Supabase table for the user's message history with limit and range
    query = supabase.table(table).select("*").eq("user_id", user_uid).order("created_at", ascending=False).range(start, start + limit - 1)
    db_res = query.execute()
    
    if db_res["data"]:
        # Extract messages and content from the response
        message_history = [{"messages": item["req"], "content": item["res"]} for item in db_res["data"]]
        return {"message_history": message_history}
    else:
        return {"message_history": []}

# Run the FastAPI server using Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, port=PORT)
