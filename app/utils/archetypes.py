from __future__ import annotations

from typing import Dict

# Categories used across archetypes
CATEGORIES = ["Technical", "Cognitive", "Values", "Behavioral", "Communication", "Leadership"]

# Top 20 roles archetypes: weights sum ~1.0; intervals are +/- 0.1 default
ARCHETYPES: Dict[str, dict] = {
	"Software Engineer": {
		"weights": {"Technical": 0.45, "Cognitive": 0.20, "Behavioral": 0.15, "Values": 0.10, "Communication": 0.07, "Leadership": 0.03},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.45, "Cognitive": 0.20, "Behavioral": 0.15, "Values": 0.10, "Communication": 0.07, "Leadership": 0.03
		}.items()},
	},
	"Data Scientist": {
		"weights": {"Technical": 0.35, "Cognitive": 0.30, "Behavioral": 0.10, "Values": 0.08, "Communication": 0.12, "Leadership": 0.05},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.35, "Cognitive": 0.30, "Behavioral": 0.10, "Values": 0.08, "Communication": 0.12, "Leadership": 0.05
		}.items()},
	},
	"Data Engineer": {
		"weights": {"Technical": 0.42, "Cognitive": 0.22, "Behavioral": 0.10, "Values": 0.08, "Communication": 0.10, "Leadership": 0.08},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.42, "Cognitive": 0.22, "Behavioral": 0.10, "Values": 0.08, "Communication": 0.10, "Leadership": 0.08
		}.items()},
	},
	"ML Engineer": {
		"weights": {"Technical": 0.40, "Cognitive": 0.25, "Behavioral": 0.10, "Values": 0.08, "Communication": 0.10, "Leadership": 0.07},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.40, "Cognitive": 0.25, "Behavioral": 0.10, "Values": 0.08, "Communication": 0.10, "Leadership": 0.07
		}.items()},
	},
	"Product Manager": {
		"weights": {"Technical": 0.15, "Cognitive": 0.25, "Behavioral": 0.20, "Values": 0.10, "Communication": 0.18, "Leadership": 0.12},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.15, "Cognitive": 0.25, "Behavioral": 0.20, "Values": 0.10, "Communication": 0.18, "Leadership": 0.12
		}.items()},
	},
	"Designer": {
		"weights": {"Technical": 0.18, "Cognitive": 0.22, "Behavioral": 0.20, "Values": 0.10, "Communication": 0.20, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.18, "Cognitive": 0.22, "Behavioral": 0.20, "Values": 0.10, "Communication": 0.20, "Leadership": 0.10
		}.items()},
	},
	"QA Engineer": {
		"weights": {"Technical": 0.35, "Cognitive": 0.22, "Behavioral": 0.12, "Values": 0.10, "Communication": 0.12, "Leadership": 0.09},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.35, "Cognitive": 0.22, "Behavioral": 0.12, "Values": 0.10, "Communication": 0.12, "Leadership": 0.09
		}.items()},
	},
	"DevOps Engineer": {
		"weights": {"Technical": 0.40, "Cognitive": 0.22, "Behavioral": 0.13, "Values": 0.10, "Communication": 0.10, "Leadership": 0.05},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.40, "Cognitive": 0.22, "Behavioral": 0.13, "Values": 0.10, "Communication": 0.10, "Leadership": 0.05
		}.items()},
	},
	"Security Engineer": {
		"weights": {"Technical": 0.42, "Cognitive": 0.23, "Behavioral": 0.12, "Values": 0.10, "Communication": 0.08, "Leadership": 0.05},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.42, "Cognitive": 0.23, "Behavioral": 0.12, "Values": 0.10, "Communication": 0.08, "Leadership": 0.05
		}.items()},
	},
	"Solutions Architect": {
		"weights": {"Technical": 0.30, "Cognitive": 0.22, "Behavioral": 0.15, "Values": 0.10, "Communication": 0.13, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.30, "Cognitive": 0.22, "Behavioral": 0.15, "Values": 0.10, "Communication": 0.13, "Leadership": 0.10
		}.items()},
	},
	"Business Analyst": {
		"weights": {"Technical": 0.12, "Cognitive": 0.25, "Behavioral": 0.20, "Values": 0.12, "Communication": 0.21, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.12, "Cognitive": 0.25, "Behavioral": 0.20, "Values": 0.12, "Communication": 0.21, "Leadership": 0.10
		}.items()},
	},
	"Recruiter": {
		"weights": {"Technical": 0.10, "Cognitive": 0.18, "Behavioral": 0.22, "Values": 0.15, "Communication": 0.25, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.10, "Cognitive": 0.18, "Behavioral": 0.22, "Values": 0.15, "Communication": 0.25, "Leadership": 0.10
		}.items()},
	},
	"HR Generalist": {
		"weights": {"Technical": 0.08, "Cognitive": 0.18, "Behavioral": 0.22, "Values": 0.20, "Communication": 0.22, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.08, "Cognitive": 0.18, "Behavioral": 0.22, "Values": 0.20, "Communication": 0.22, "Leadership": 0.10
		}.items()},
	},
	"Sales Executive": {
		"weights": {"Technical": 0.10, "Cognitive": 0.20, "Behavioral": 0.20, "Values": 0.10, "Communication": 0.25, "Leadership": 0.15},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.10, "Cognitive": 0.20, "Behavioral": 0.20, "Values": 0.10, "Communication": 0.25, "Leadership": 0.15
		}.items()},
	},
	"Account Manager": {
		"weights": {"Technical": 0.12, "Cognitive": 0.20, "Behavioral": 0.22, "Values": 0.12, "Communication": 0.24, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.12, "Cognitive": 0.20, "Behavioral": 0.22, "Values": 0.12, "Communication": 0.24, "Leadership": 0.10
		}.items()},
	},
	"Marketing Manager": {
		"weights": {"Technical": 0.12, "Cognitive": 0.22, "Behavioral": 0.18, "Values": 0.13, "Communication": 0.25, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.12, "Cognitive": 0.22, "Behavioral": 0.18, "Values": 0.13, "Communication": 0.25, "Leadership": 0.10
		}.items()},
	},
	"Finance Analyst": {
		"weights": {"Technical": 0.25, "Cognitive": 0.30, "Behavioral": 0.12, "Values": 0.12, "Communication": 0.16, "Leadership": 0.05},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.25, "Cognitive": 0.30, "Behavioral": 0.12, "Values": 0.12, "Communication": 0.16, "Leadership": 0.05
		}.items()},
	},
	"Operations Manager": {
		"weights": {"Technical": 0.15, "Cognitive": 0.25, "Behavioral": 0.18, "Values": 0.12, "Communication": 0.18, "Leadership": 0.12},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.15, "Cognitive": 0.25, "Behavioral": 0.18, "Values": 0.12, "Communication": 0.18, "Leadership": 0.12
		}.items()},
	},
	"Customer Support": {
		"weights": {"Technical": 0.10, "Cognitive": 0.18, "Behavioral": 0.24, "Values": 0.15, "Communication": 0.23, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.10, "Cognitive": 0.18, "Behavioral": 0.24, "Values": 0.15, "Communication": 0.23, "Leadership": 0.10
		}.items()},
	},
	"IT Support": {
		"weights": {"Technical": 0.32, "Cognitive": 0.20, "Behavioral": 0.15, "Values": 0.12, "Communication": 0.13, "Leadership": 0.08},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.32, "Cognitive": 0.20, "Behavioral": 0.15, "Values": 0.12, "Communication": 0.13, "Leadership": 0.08
		}.items()},
	},
	"Project Manager": {
		"weights": {"Technical": 0.18, "Cognitive": 0.22, "Behavioral": 0.20, "Values": 0.12, "Communication": 0.18, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.18, "Cognitive": 0.22, "Behavioral": 0.20, "Values": 0.12, "Communication": 0.18, "Leadership": 0.10
		}.items()},
	},
	"Content Writer": {
		"weights": {"Technical": 0.10, "Cognitive": 0.20, "Behavioral": 0.18, "Values": 0.12, "Communication": 0.30, "Leadership": 0.10},
		"intervals": {k: {"min": max(0.0, v - 0.10), "max": min(1.0, v + 0.10)} for k, v in {
			"Technical": 0.10, "Cognitive": 0.20, "Behavioral": 0.18, "Values": 0.12, "Communication": 0.30, "Leadership": 0.10
		}.items()},
	},
}
