"""Starter placeholder for difficulty estimation logic."""


def estimate_difficulty(prompt: str) -> dict:
    prompt_lower = prompt.lower()
    words = prompt_lower.split()
    word_count = len(words)

    score = 0
    reasons = []

    #length based scoring 
    if word_count <= 8:
        score += 1
        reasons.append("Short prompt")

    elif word_count <= 25:
        score += 3
        reasons.append("Medium-length prompt")
    else:
        score += 5
        reasons.append("Long prompt with more context")

    #keyword based scoring 
    hard_keywords = [
        "architecture", "scalable", "optimize", "debug", "implement",
        "production", "latency", "database", "api", "security",
        "algorithm", "system design", "performance", "deployment"
    ]

    medium_keywords = [
        "explain", "summarize", "compare", "example", "steps",
        "guide", "rewrite", "analyze", "learn"
    ]


    for keyword in hard_keywords:
        if keyword in prompt_lower:
            score += 3
            reasons.append(f"Contains hard keyword: '{keyword}'")
            break

    for keyword in medium_keywords:
        if keyword in prompt_lower:
            score += 2
            reasons.append(f"Contains medium keyword: '{keyword}'")
            break
    
    #multi task detections

    connectors = ["and", "also", "then", "after that", "next","with"]

    connector_count = 0
    for connector in connectors:
        if connector in words:
            connector_count += 1

    if connector_count >= 2:
        score += 2
        reasons.append("Multiple connectors detected, indicating multiple tasks")
    
    #output expectations 
    output_keywords = ["code", "formula", "diagram", "table", "api", "test", "examples"]

    for keyword in output_keywords:
        if keyword in prompt_lower:
            score += 2
            reasons.append(f"Output expectation detected: '{keyword}'")
            break

    #final difficulty label

    if score <= 3:
        difficulty = "easy"
    elif score <= 7:
        difficulty = "medium"
    else:
        difficulty = "hard" 

    return {
        "difficulty": difficulty,
        "score": score,
        "reasons": reasons
    }

