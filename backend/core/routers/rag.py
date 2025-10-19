from ninja import Schema, Router, Body
from typing import List
from ..rag.services import answer_question

rag_router = Router()

# Define schemas for the input RAG query and the output answer to return.
class QuerySchema(Schema):
    query: str

class AnswerSchema(Schema):
    answer: str
    sources: List[str]

# NOTE: We use 'Body' here to simplify the JSONify operation on the client-side.
# We can essentially skip over some of the nested JSON and only pass in the query.
@rag_router.post("/queryTranscripts", response=AnswerSchema)
def query_transcripts(request, payload: QuerySchema = Body(...)):
    """
    Query the RAG DB and retrieve a coherent response.
    """

    result = answer_question(payload.query)
    return result
