"""Vercel Serverless Function for Style Checker API"""
import json
import re
from http.server import BaseHTTPRequestHandler


# Style rules
STYLE_RULES = {
    "vague_terms": [
        "significant", "substantial", "considerable", "notable",
        "good progress", "great progress", "some progress",
        "many", "several", "various", "a lot", "lots of",
        "soon", "shortly", "eventually", "later"
    ],
    "pet_peeves": [
        "sorry to bother", "quick sync", "just checking in",
        "touching base", "circle back", "ping you", "loop you in"
    ]
}


def check_bluf_structure(text):
    lines = text.strip().split('\n')
    if not lines:
        return None
    first_line = lines[0].lower()
    bluf_indicators = ["status:", "decision:", "ask:", "summary:", "tldr:", "tl;dr:",
                       "recommendation:", "request:", "update:", "issue:", "action:"]
    has_bluf = any(ind in first_line for ind in bluf_indicators)
    context_starters = ["as you know", "i wanted to", "i'm writing to", "following up",
                        "per our", "regarding", "in reference", "as discussed"]
    starts_with_context = any(first_line.startswith(cs) for cs in context_starters)
    if not has_bluf and starts_with_context:
        return {
            "category": "Structure",
            "issue": "Message doesn't lead with the main point",
            "suggestion": "Start with the conclusion, decision, or ask. Add context after.",
            "severity": "high"
        }
    return None


def check_passive_voice(text):
    patterns = [r"\b(was|were|been|being|is|are|am)\s+\w+ed\b", r"\b(has|have|had)\s+been\s+\w+ed\b"]
    issues = []
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if len(matches) > 2:
            issues.append({
                "category": "Clarity",
                "issue": f"Excessive passive voice detected ({len(matches)} instances)",
                "suggestion": "Use active voice. E.g., 'The team completed...' instead of 'It was completed...'",
                "severity": "medium"
            })
            break
    return issues


def check_vague_terms(text):
    issues = []
    text_lower = text.lower()
    found_terms = [term for term in STYLE_RULES["vague_terms"] if term in text_lower]
    if found_terms:
        issues.append({
            "category": "Specificity",
            "issue": f"Vague terms found: {', '.join(found_terms[:3])}{'...' if len(found_terms) > 3 else ''}",
            "suggestion": "Replace with specific numbers. E.g., 'significant improvement' → '35% improvement'",
            "severity": "medium"
        })
    return issues


def check_action_items(text):
    text_lower = text.lower()
    action_patterns = [r"\b(next steps?|action items?|todo|to-do)\b", r"\b(will|shall)\s+\w+\b"]
    has_action_items = any(re.search(p, text_lower) for p in action_patterns)
    word_count = len(text.split())
    if word_count > 50 and not has_action_items:
        return {
            "category": "Actionability",
            "issue": "No clear action items or next steps detected",
            "suggestion": "Add a 'Next Steps' section with specific actions, owners, and deadlines",
            "severity": "high"
        }
    return None


def check_pet_peeves(text):
    issues = []
    text_lower = text.lower()
    for term in STYLE_RULES["pet_peeves"]:
        if term in text_lower:
            issues.append({
                "category": "Tone",
                "issue": f"Pet peeve phrase detected: '{term}'",
                "suggestion": "Be direct. State the specific topic and ask.",
                "severity": "low"
            })
    return issues


def check_over_apologizing(text):
    issues = []
    text_lower = text.lower()
    patterns = [r"\bsorry\b.*\bsorry\b", r"\bapologize\b.*\bapologize\b", r"^sorry\b"]
    for pattern in patterns:
        if re.search(pattern, text_lower):
            issues.append({
                "category": "Tone",
                "issue": "Over-apologizing detected",
                "suggestion": "Reduce apologies. State issues directly and move to the solution.",
                "severity": "low"
            })
            break
    return issues


def calculate_style_score(issues):
    score = 100
    for issue in issues:
        if issue["severity"] == "high":
            score -= 20
        elif issue["severity"] == "medium":
            score -= 10
        else:
            score -= 5
    return max(0, score)


def generate_summary(score, issues):
    if score >= 85:
        return "Excellent! Your message follows the communication style guidelines well."
    elif score >= 70:
        return "Good structure, but consider the suggestions above for improvement."
    elif score >= 50:
        return "Several areas need attention. Review the issues and apply the suggestions."
    return "This message needs significant revision to align with communication guidelines."


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            text = data.get('text', '')
            
            if not text.strip():
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Text cannot be empty"}).encode())
                return
            
            issues = []
            bluf_issue = check_bluf_structure(text)
            if bluf_issue:
                issues.append(bluf_issue)
            issues.extend(check_passive_voice(text))
            issues.extend(check_vague_terms(text))
            action_issue = check_action_items(text)
            if action_issue:
                issues.append(action_issue)
            issues.extend(check_pet_peeves(text))
            issues.extend(check_over_apologizing(text))
            
            score = calculate_style_score(issues)
            summary = generate_summary(score, issues)
            
            response = {
                "score": score,
                "issues": issues,
                "summary": summary,
                "improved_version": None
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
