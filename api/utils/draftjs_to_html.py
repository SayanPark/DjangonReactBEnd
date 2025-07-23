import json
from html import escape

def draftjs_to_html(draftjs_json_str):
    """
    Convert Draft.js JSON content to HTML string.
    This is a simple converter that handles unstyled blocks and inline styles.
    For complex content, consider using a dedicated library.
    """
    try:
        content = json.loads(draftjs_json_str)
    except json.JSONDecodeError:
        return escape(draftjs_json_str)  # Return escaped raw string if JSON invalid

    blocks = content.get("blocks", [])
    html_parts = []

    for block in blocks:
        text = escape(block.get("text", ""))
        block_type = block.get("type", "unstyled")

        if block_type == "unstyled":
            html_parts.append(f"<p>{text}</p>")
        elif block_type == "header-one":
            html_parts.append(f"<h1>{text}</h1>")
        elif block_type == "header-two":
            html_parts.append(f"<h2>{text}</h2>")
        elif block_type == "blockquote":
            html_parts.append(f"<blockquote>{text}</blockquote>")
        else:
            # Default fallback
            html_parts.append(f"<p>{text}</p>")

    return "\n".join(html_parts)
