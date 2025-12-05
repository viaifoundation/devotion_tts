import sys
import markdown

# Read Markdown from stdin
markdown_text = sys.stdin.read()

# Convert Markdown to HTML
html_output = markdown.markdown(markdown_text)

# Output the HTML to stdout
print(html_output)
