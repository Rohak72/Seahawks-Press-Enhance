from django.conf import settings
import openai
import json

# Configure the OpenAI client with our custom Groq API key.
client = openai.OpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

def generate_video_summary(transcript_text: str):
    """
    Converts the Whisper transcript into a comprehensive summary, presented as a punchy one-liner,
    3-5 bullet points, and a full-length paragraph.
    """
    
    try:
        # The system-user role combination here helps the AI model prioritize/remember the core components of
        # the summary task and digest the complex specifics of the user prompt.
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": "You are an experienced sports analyst. Your task is to generate a structured summary from "
                 "the provided press conference transcript. The output must be a valid JSON object."},
                 {"role": "user",
                  "content": f"""Analyze the following transcript and generate a summary. Return a JSON object with 
                  three keys: 'title' (a catchy, newspaper-style headline), 'one_sentence_summary' (a single, concise 
                  sentence), and 'key_bullet_points' (a list of 3-5 important string bullet points). Make sure that
                  the bullets are information dense and cover all the key quotes / takeaways, not just regurgitating
                  the contents of the title and one-liner.

                  SPECIFIC INSTRUCTIONS:
                  1.  Generate a JSON object with three keys: "title", "one_sentence_summary", and "key_bullet_points".
                  2.  The "key_bullet_points" value must be a JSON list of strings.
                  3.  CRITICAL: Ensure all strings inside the JSON are properly formatted. Correctly escape any special 
                  characters like quotes (") or newlines (\\n).
                  4.  DO NOT output any text, explanation, or markdown formatting before or after the JSON object. 
                  Your entire response must be only the JSON.
                  
                  Transcript: {transcript_text}"""}
            ]
        )

        summary_dict = json.loads(response.choices[0].message.content)
        return summary_dict

    except Exception as e:
        print(f"LLM failed to generate summary: {e}!")
        return {"error": str(e)}
    
def generate_master_summary(summaries: list[str]) -> str:
    """
    Analyze multiple video summaries to produce a roundup that can be fed into TTS.
    """

    print("LLM Service (Groq): Generating master daily digest script...")
    
    combined_summaries = "\n".join(f"- {s}" for s in summaries)

    prompt = f"""You are a sports podcast host for the "Seahawks Daily Digest". Your task is to write a short, 
    engaging monologue that summarizes the key points from today's press conferences. The monologue should be 
    approximately 150-200 words.

    KEY POINTS FROM TODAY:
    {combined_summaries}

    INSTRUCTIONS:
    - Write a natural, conversational script suitable for a podcast.
    - Start with a welcome, like "Welcome to the Seahawks Daily Digest for October 16th."
    - Weave the key points together into a coherent narrative. Do not just list them.
    - Maintain a professional and engaging tone.
    - End with a sign-off, like "That's the latest from the Seahawks sideline. Tune in next time for your daily digest."
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"!!! LLM Error in generate_master_summary (Groq): {e} !!!")
        raise