"""Communication style checker service."""
import re
from typing import Optional


# Style rules extracted from communication_style.md
STYLE_RULES = {
    "bluf": {
        "description": "Bottom Line Up Front - lead with the conclusion",
        "severity": "high"
    },
    "passive_voice": {
        "description": "Avoid passive voice to maintain accountability",
        "severity": "medium",
        "patterns": [
            r"\b(was|were|been|being|is|are|am)\s+\w+ed\b",
            r"\b(has|have|had)\s+been\s+\w+ed\b"
        ]
    },
    "vague_terms": {
        "description": "Use specific metrics instead of vague terms",
        "severity": "medium",
        "terms": [
            "significant", "substantial", "considerable", "notable",
            "good progress", "great progress", "some progress",
            "many", "several", "various", "a lot", "lots of",
            "soon", "shortly", "eventually", "later"
        ]
    },
    "action_items": {
        "description": "Include clear next steps with owners",
        "severity": "high",
        "positive_patterns": [
            r"\b(next steps?|action items?|todo|to-do)\b",
            r"\b(will|shall)\s+\w+\b",
            r"\[@\w+\]",  # @mentions
            r"\b(by|deadline|due)\s+\w+day\b"
        ]
    },
    "metrics": {
        "description": "Quantify impact with specific numbers",
        "severity": "medium",
        "positive_patterns": [
            r"\d+%",
            r"\d+\s*(hours?|days?|weeks?|months?)",
            r"\$\d+",
            r"\d+\s*(users?|customers?|requests?|errors?)"
        ]
    },
    "pet_peeves": {
        "description": "Avoid known pet peeves",
        "severity": "low",
        "terms": [
            "sorry to bother",
            "quick sync",
            "just checking in",
            "touching base",
            "circle back",
            "ping you",
            "loop you in"
        ]
    },
    "over_apologizing": {
        "description": "Don't over-apologize",
        "severity": "low",
        "patterns": [
            r"\bsorry\b.*\bsorry\b",
            r"\bapologize\b.*\bapologize\b",
            r"^sorry\b"
        ]
    }
}


def check_bluf_structure(text: str) -> Optional[dict]:
    """Check if text follows BLUF (Bottom Line Up Front) structure."""
    lines = text.strip().split('\n')
    if not lines:
        return None
    
    first_line = lines[0].lower()
    
    # Indicators of BLUF structure
    bluf_indicators = [
        "status:", "decision:", "ask:", "summary:", "tldr:", "tl;dr:",
        "recommendation:", "request:", "update:", "issue:", "action:"
    ]
    
    has_bluf = any(ind in first_line for ind in bluf_indicators)
    
    # Check if first sentence is a conclusion vs. context
    context_starters = [
        "as you know", "i wanted to", "i'm writing to", "following up",
        "per our", "regarding", "in reference", "as discussed"
    ]
    starts_with_context = any(first_line.startswith(cs) for cs in context_starters)
    
    if not has_bluf and starts_with_context:
        return {
            "category": "Structure",
            "issue": "Message doesn't lead with the main point",
            "suggestion": "Start with the conclusion, decision, or ask. Add context after.",
            "severity": "high"
        }
    
    return None


def check_passive_voice(text: str) -> list[dict]:
    """Detect passive voice usage."""
    issues = []
    
    for pattern in STYLE_RULES["passive_voice"]["patterns"]:
        matches = re.findall(pattern, text.lower())
        if len(matches) > 2:  # Only flag if excessive
            issues.append({
                "category": "Clarity",
                "issue": f"Excessive passive voice detected ({len(matches)} instances)",
                "suggestion": "Use active voice to maintain accountability. E.g., 'The team completed...' instead of 'It was completed...'",
                "severity": "medium"
            })
            break
    
    return issues


def check_vague_terms(text: str) -> list[dict]:
    """Detect vague terms that should be quantified."""
    issues = []
    text_lower = text.lower()
    
    found_terms = []
    for term in STYLE_RULES["vague_terms"]["terms"]:
        if term in text_lower:
            found_terms.append(term)
    
    if found_terms:
        issues.append({
            "category": "Specificity",
            "issue": f"Vague terms found: {', '.join(found_terms[:3])}{'...' if len(found_terms) > 3 else ''}",
            "suggestion": "Replace with specific numbers. E.g., 'significant improvement' → '35% improvement'",
            "severity": "medium"
        })
    
    return issues


def check_action_items(text: str) -> Optional[dict]:
    """Check if text includes clear action items."""
    text_lower = text.lower()
    
    # Check for positive action item indicators
    has_action_items = any(
        re.search(pattern, text_lower)
        for pattern in STYLE_RULES["action_items"]["positive_patterns"]
    )
    
    # For longer messages, expect action items
    word_count = len(text.split())
    if word_count > 50 and not has_action_items:
        return {
            "category": "Actionability",
            "issue": "No clear action items or next steps detected",
            "suggestion": "Add a 'Next Steps' section with specific actions, owners, and deadlines",
            "severity": "high"
        }
    
    return None


def check_metrics(text: str) -> Optional[dict]:
    """Check if text includes quantified metrics."""
    # Check for positive metric indicators
    has_metrics = any(
        re.search(pattern, text)
        for pattern in STYLE_RULES["metrics"]["positive_patterns"]
    )
    
    # For status-like messages, expect metrics
    status_indicators = ["update", "progress", "status", "report", "weekly"]
    text_lower = text.lower()
    is_status_message = any(ind in text_lower for ind in status_indicators)
    
    if is_status_message and not has_metrics:
        return {
            "category": "Data",
            "issue": "Status update lacks quantified metrics",
            "suggestion": "Include specific numbers: completion %, time spent, items remaining, etc.",
            "severity": "medium"
        }
    
    return None


def check_pet_peeves(text: str) -> list[dict]:
    """Check for communication pet peeves."""
    issues = []
    text_lower = text.lower()
    
    for term in STYLE_RULES["pet_peeves"]["terms"]:
        if term in text_lower:
            issues.append({
                "category": "Tone",
                "issue": f"Pet peeve phrase detected: '{term}'",
                "suggestion": "Be direct. Instead of 'quick sync', state the specific topic and ask.",
                "severity": "low"
            })
    
    return issues


def check_over_apologizing(text: str) -> list[dict]:
    """Check for over-apologizing."""
    issues = []
    text_lower = text.lower()
    
    for pattern in STYLE_RULES["over_apologizing"]["patterns"]:
        if re.search(pattern, text_lower):
            issues.append({
                "category": "Tone",
                "issue": "Over-apologizing detected",
                "suggestion": "Reduce apologies. If something needs addressing, state it directly and move to the solution.",
                "severity": "low"
            })
            break
    
    return issues


def calculate_style_score(issues: list[dict]) -> int:
    """Calculate overall style score based on issues found."""
    score = 100
    
    for issue in issues:
        if issue["severity"] == "high":
            score -= 20
        elif issue["severity"] == "medium":
            score -= 10
        else:
            score -= 5
    
    return max(0, score)


def generate_summary(score: int, issues: list[dict]) -> str:
    """Generate a summary of the style check."""
    if score >= 85:
        return "Excellent! Your message follows the communication style guidelines well."
    elif score >= 70:
        return "Good structure, but consider the suggestions above for improvement."
    elif score >= 50:
        return "Several areas need attention. Review the issues and apply the suggestions."
    else:
        return "This message needs significant revision to align with communication guidelines."


def check_communication_style(text: str) -> dict:
    """
    Main function to check text against communication style guidelines.
    Returns a comprehensive style check result.
    """
    issues = []
    
    # Run all checks
    bluf_issue = check_bluf_structure(text)
    if bluf_issue:
        issues.append(bluf_issue)
    
    issues.extend(check_passive_voice(text))
    issues.extend(check_vague_terms(text))
    
    action_issue = check_action_items(text)
    if action_issue:
        issues.append(action_issue)
    
    metric_issue = check_metrics(text)
    if metric_issue:
        issues.append(metric_issue)
    
    issues.extend(check_pet_peeves(text))
    issues.extend(check_over_apologizing(text))
    
    # Calculate score and summary
    score = calculate_style_score(issues)
    summary = generate_summary(score, issues)
    
    return {
        "score": score,
        "issues": issues,
        "summary": summary,
        "improved_version": None  # Could add AI-powered rewriting in future
    }
