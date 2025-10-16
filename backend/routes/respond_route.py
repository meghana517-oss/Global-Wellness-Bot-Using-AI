from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime

from backend.utils.dependencies import get_db, get_current_user
from backend.main import Message
from backend.dialogue_state_machine import DialogueStateMachine
from backend.dialogue_manager import infer_intents

respond_router = APIRouter()
state_machine = DialogueStateMachine()

# -----------------------
# Request & Response Schemas
# -----------------------
class RespondRequest(BaseModel):
    text: str
    intent: Optional[List[str]] = []
    confidence_scores: Optional[Dict[str, float]] = {}

class RespondResponse(BaseModel):
    response: str
    intent: List[str]
    confidence_scores: Dict[str, float]

# -----------------------
# Respond Endpoint
# -----------------------
@respond_router.post("/respond", response_model=RespondResponse)
def respond(
    request: RespondRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # ✅ Step 1: Infer intent if not provided
    intents = request.intent if request.intent else infer_intents(request.text)
    confidence_scores = request.confidence_scores or {}

    # ✅ Step 2: Use DialogueStateMachine for each intent
    responses = []
    final_intents = []

    for intent in intents:
        confidence = confidence_scores.get(intent, 1.0)
        reply, resolved_intent = state_machine.transition(intent, request.text, confidence)
        if reply:
            responses.append(reply)
            final_intents.append(resolved_intent)

    # ✅ Step 3: Fallback if no response
    if not responses:
        responses.append("I'm here to help—could you clarify your question?")
        final_intents = intents

    # ✅ Step 4: Join responses into a single string
    reply_text = "\n\n".join(responses)

    # ✅ Step 5: Log message to DB
    message = Message(
        email="anonymous",
        user_text=request.text,
        bot_response=reply,
        intent=", ".join(request.intent),  # ✅ Save intent history
        timestamp=datetime.utcnow()
        )

    db.add(message)
    db.commit()

    # ✅ Step 6: Return response
    return {
        "response": reply_text,
        "intent": final_intents,
        "confidence_scores": confidence_scores
    }
