# CLAUDE.md

This file provides guidance for Claude when working on this codebase.

## Project Overview

An arXiv paper tracking system that fetches papers daily, analyzes them with LLM, and generates a static website.

## Tech Stack

- Python 3.11+
- Pydantic v2 for data models
- Jinja2 for templating
- Click for CLI
- arxiv.py for arXiv API
- Multi-LLM support: Claude, OpenAI, Ollama

## Code Style

- Use type hints for all function signatures
- Use Pydantic models for data validation
- Keep functions focused and small
- Use f-strings for string formatting
- Follow PEP 8 naming conventions

## Important Patterns

### Configuration
- All user configuration lives in `data/config.json`
- Use environment variables for secrets (API keys)
- Config is loaded via `src/config.py`

### LLM Analyzers
- All analyzers inherit from `BaseAnalyzer` in `src/llm/base.py`
- Implement `_call_llm(prompt: str) -> str` method
- Use `get_analyzer(config)` factory function

### Data Flow
1. `ArxivFetcher` produces `RawPaper` objects
2. `BaseAnalyzer.analyze_paper()` produces `AnalysisResult`
3. `AnalyzedPaper.from_raw_and_analysis()` combines them
4. `save_daily_papers()` persists to JSON
5. `SiteGenerator.generate()` creates static HTML

## Testing

Run with dry-run flag to test without LLM:
```bash
python -m src.main fetch-and-analyze --dry-run
```

## Common Tasks

### Adding a new LLM provider
1. Create `src/llm/new_analyzer.py`
2. Inherit from `BaseAnalyzer`
3. Implement `_call_llm()` method
4. Add to `src/llm/__init__.py`
5. Update `get_analyzer()` function

### Adding a new domain
Edit `data/config.json` and add to `domains` array.

## Files Not to Modify

- `docs/` - Auto-generated, will be overwritten
- `data/papers/*.json` - Auto-generated paper data
