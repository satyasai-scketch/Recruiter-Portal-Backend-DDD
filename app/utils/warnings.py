from __future__ import annotations

from typing import Dict, List


# Prewritten templates keyed by category and direction (low/high)
WARNING_TEMPLATES: Dict[str, Dict[str, str]] = {
	"Technical": {
		"low": "Lowering Technical below {min:.0%} may exclude core skills and tool proficiency.",
		"high": "Raising Technical above {max:.0%} may overweight hard skills and filter out adaptable talent.",
	},
	"Cognitive": {
		"low": "Cognitive below {min:.0%} may reduce emphasis on problem-solving and learning agility.",
		"high": "Cognitive above {max:.0%} may overshadow practical experience and delivery track record.",
	},
	"Values": {
		"low": "Values below {min:.0%} may weaken culture alignment and retention likelihood.",
		"high": "Values above {max:.0%} may underweight execution capability and speed to impact.",
	},
	"Behavioral": {
		"low": "Behavioral below {min:.0%} may overlook collaboration and stakeholder management.",
		"high": "Behavioral above {max:.0%} may underweight technical autonomy and depth.",
	},
	"Leadership": {
		"low": "Leadership below {min:.0%} may limit team direction and decision velocity.",
		"high": "Leadership above {max:.0%} may underweight hands-on contribution and detail orientation.",
	},
	"Communication": {
		"low": "Communication below {min:.0%} may hinder cross-functional alignment and clarity.",
		"high": "Communication above {max:.0%} may underweight deep work and builder mindset.",
	},
}


def render_weight_warnings(weights: Dict[str, float], intervals: Dict[str, dict]) -> List[str]:
	"""Render human-readable warnings for any category outside its interval.

	Intervals use a dict form: {"min": float, "max": float}
	"""
	messages: List[str] = []
	for cat, w in (weights or {}).items():
		interval = intervals.get(cat)
		if not interval:
			continue
		min_v, max_v = float(interval.get("min", 0.0)), float(interval.get("max", 1.0))
		if w < min_v:
			msg = WARNING_TEMPLATES.get(cat, {}).get("low") or f"{cat} below recommended {min_v:.0%}."
			messages.append(msg.format(min=min_v, max=max_v))
		elif w > max_v:
			msg = WARNING_TEMPLATES.get(cat, {}).get("high") or f"{cat} above recommended {max_v:.0%}."
			messages.append(msg.format(min=min_v, max=max_v))
	return messages
