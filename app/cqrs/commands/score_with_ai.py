from .base import Command


class ScoreCandidateWithAI(Command):
    """Command to score a candidate using AI service"""
    
    def __init__(self, candidate_id: str, persona_id: str, cv_id: str):
        self.candidate_id = candidate_id
        self.persona_id = persona_id
        self.cv_id = cv_id