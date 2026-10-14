"""Service kiểm tra điều kiện học, độc lập với ranking."""


from app.rules import eligible_courses, evaluate_eligibility

__all__ = ["eligible_courses", "evaluate_eligibility"]
