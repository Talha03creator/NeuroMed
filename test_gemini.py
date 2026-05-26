import asyncio
from google import genai
from google.genai import types

async def main():
    client = genai.Client(api_key='AIzaSyCjFMDZY1z9xd5ogCePJ2SzZPVOOZH0VoE')
    try:
        print("Testing async call via client.aio.models.generate_content...")
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents='Say hello in one sentence.',
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=50)
        )
        print('SUCCESS:', response.text)
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}')

asyncio.run(main())
