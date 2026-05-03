# look_at Tool

## Description

The `look_at` tool extracts basic information from media files (PDFs, images, diagrams) when a quick summary suffices over precise reading. It's designed for simple text-based content extraction without requiring the full Read tool.

⚠️ **Important Limitations**:
- NEVER use for visual precision, aesthetic evaluation, or exact accuracy
- Use the Read tool instead for cases requiring visual precision or exact accuracy
- This tool is read-only and does not modify any files

## Usage

```bash
look_at(
    file_path: str,  # Absolute path to the file to analyze
    goal: str        # What specific information to extract from the file
)

# OR for clipboard/pasted images:
look_at(
    image_data: str, # Base64 encoded image data
    goal: str        # What specific information to extract from the image
)
```

## Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `file_path` | string | Absolute path to the file to analyze | Yes (if no `image_data`) |
| `image_data` | string | Base64 encoded image data (for clipboard/pasted images) | Yes (if no `file_path`) |
| `goal` | string | What specific information to extract from the file | Yes |

## Examples

### Extract text from a PDF
```python
look_at(
    file_path="/path/to/document.pdf",
    goal="Extract the main headings and key points from this document"
)
```

### Analyze a screenshot
```python
look_at(
    file_path="/path/to/screenshot.png",
    goal="Identify the main UI elements visible in this screenshot"
)
```

### Analyze a clipboard image
```python
look_at(
    image_data="base64_encoded_data_here",
    goal="Extract any visible text from this image"
)
```

## Technical Details

- **Implementation**: Uses multimodal model analysis via the registered `multimodal-looker` model
- **Model**: Uses the agent's configured vision-capable model (nvidia/nvidia/nemotron-3-nano-omni)
- **Output**: Returns clean text content extracted from the file
- **Performance**: Optimized for quick analysis rather than precise extraction

## When to Use

✅ **Good for**:
- Quick text extraction from PDFs
- Basic content analysis of images
- Simple diagram understanding
- Fast content summaries

❌ **Not for**:
- Visual precision tasks
- Aesthetic evaluation
- Exact layout analysis
- Complex document processing
- Any task requiring pixel-perfect accuracy

## Best Practices

1. **Be specific** in your `goal` parameter to get the most relevant information
2. **Use Read tool** when you need precise, detailed analysis
3. **Combine with other tools** for comprehensive analysis workflows
4. **Handle errors gracefully** - the tool may fail on complex or unsupported file formats

## Error Handling

The tool may return errors for:
- Unsupported file formats
- Corrupted files
- Permission issues
- Model resolution failures
- Network connectivity issues (for cloud-based analysis)

Always check the error output and fall back to the Read tool if `look_at` fails to provide adequate results.