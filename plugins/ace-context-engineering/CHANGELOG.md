# Changelog

All notable changes to the ACE Context Engineering plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-10-27

### Fixed
- **CRITICAL**: Fixed data loss bug in ClaudeCodeACE.reflect() that was discarding execution_feedback
  - Root cause: reflect() method was recreating execution_result dictionary, losing error_analysis data
  - Impact: Reflector was receiving empty error_analysis despite AppWorldExecutor populating it correctly
  - Solution: Store full execution_result in generate(), retrieve it in reflect()
- Fixed Reflector early exit bug that skipped bullet generation for failures when missing_guidance was empty
  - Changed condition from `if not missing_guidance and success` to `if success`
- Fixed logic_error handling to always generate bullets instead of returning None
  - Now creates generic bullet from instruction context when missing_patterns is empty
  - Ensures organic bullet discovery from all logic errors

### Changed
- Enhanced plugin description to highlight fixed bullet discovery enabling organic learning

### Verified
- 1-sample test: Successfully generated 1 bullet (5 → 6 bullets)
- 100-task production evaluation: Confirmed organic bullet generation in real-time
- Playbook growth: 5 seed bullets → 8 bullets (+3 discovered organically)
- helpful_count: 178 and incrementing (bullets actively used)

### Documentation
- Added BUGFIX_COMPLETE.md with comprehensive root cause analysis
- Added MISSION_ACCOMPLISHED.md with final status report
- Detailed investigation methodology and verification results

## [2.0.0] - 2025-10-26

### Added
- Three-stage FAISS-based curator with quality gating
- AppWorld executor integration with TGC/SGC metrics
- Multi-epoch offline learning with grow-and-refine mechanism
- Semantic similarity-based deduplication (384-dim embeddings)
- Anthropic and Gemini LLM support for code generation
- Comprehensive evaluation framework for AppWorld benchmark

### Changed
- Migrated from v1.0 single-file playbook to modular architecture
- Implemented structured bullet/delta schema with evidence tracking
- Enhanced retrieval with FAISS semantic search

### Features
- **three_stage_curator**: Structural validation, FAISS deduplication, final approval (stable)
- **faiss_deduplication**: Sentence transformer-based duplicate detection (stable)
- **appworld_executor**: Real task execution with metrics (beta)
- **offline_learning**: Multi-epoch training (stable)

## [1.0.0] - 2025-10-25

### Added
- Initial release of ACE Context Engineering plugin
- Basic bullet retrieval and playbook management
- Simple code generation for AppWorld tasks
- Offline adaptation framework

---

**Note**: Versions 2.0.1+ demonstrate production-ready organic bullet discovery from task failures, enabling continuous learning as described in the ACE paper.
