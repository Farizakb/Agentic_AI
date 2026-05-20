import re

def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a given text.
    Attempts to use tiktoken with the gpt-4o-mini encoder if available.
    Otherwise, falls back to a character count approximation (4 characters per token).
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        return len(encoding.encode(text))
    except ImportError:
        # 4 characters per token is a standard heuristic for English text
        return len(text) // 4


def truncate_history_to_budget(history: list, prompt: str, max_tokens: int = 10000) -> list:
    """
    Prunes the execution history to fit within a specified token budget.
    Iterates backward from the most recent step to ensure that the newest
    and most relevant context is preserved. Older steps are either truncated
    or omitted once the budget is exceeded.
    """
    base_prompt_tokens = estimate_tokens(f"📘 User Prompt:\n{prompt}\n\n📜 History so far:\n")
    if base_prompt_tokens >= max_tokens:
        # If the user prompt alone is larger than the budget, return the history as empty
        # to at least allow some room, though it's an extreme case.
        return []

    remaining_budget = max_tokens - base_prompt_tokens
    trimmed_history = []
    
    # Process history from newest to oldest
    for item in reversed(history):
        # Handle history items (desc, agent, output)
        desc, agent, output = item[0], item[1], item[2]
        
        # Estimate the entry overhead (headers/formatting)
        entry_overhead_text = f"\n🧩 Other (Step X) by {agent}:\n\n"
        entry_overhead_tokens = estimate_tokens(entry_overhead_text)
        
        if remaining_budget <= entry_overhead_tokens:
            # No budget left for this step at all
            break
            
        remaining_budget -= entry_overhead_tokens
        output_tokens = estimate_tokens(output)
        
        if output_tokens <= remaining_budget:
            # We can afford the entire step output
            trimmed_history.insert(0, [desc, agent, output])
            remaining_budget -= output_tokens
        else:
            # We must truncate the step output to fit the remaining budget
            # Approximate character length we can afford
            char_budget = remaining_budget * 4
            if char_budget > 100:
                truncated_output = output[:char_budget] + "\n... [truncated to fit token budget] ..."
                trimmed_history.insert(0, [desc, agent, truncated_output])
            # Budget is now exhausted
            break
            
    return trimmed_history
