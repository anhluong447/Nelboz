# Nelboz — Facebook Automation Bot

Nelboz is a personal engineering and research automation project focused on Computer Vision, lightweight Machine Learning, and OS-level interaction.

It automates feed interactions (commenting on new feed posts and context-aware thread replies) by controlling real Google Chrome at the operating system level, without touching the Facebook DOM or internal APIs.

## Key Technical Highlights
- **OS-Level Control**: Screen capture via `mss` and human-like input simulation via `pynput` (cubic Bézier trajectories, stochastic typing intervals, and natural delays).
- **Lightweight & Custom CV**: Designed to minimize heavy pretrained models in favor of custom-trained, domain-specific vision modules (background-segmentation, UI anchor detection, custom CRNN OCR).
- **Two-Tier Intelligence**: Cheap NLP pre-filtering (TF-IDF + Logistic Regression) paired with cloud LLMs enforcing structured JSON schemas.
- **Clean Architecture**: Decoupled Domain, Application, and Infrastructure layers using Ports & Adapters for seamless testing and mocking.

## Project Structure
- `src/domain/`: Core business entities and abstract port interfaces.
- `src/application/`: Flow A (`FeedCommentUseCase`) and Flow B (`ThreadReplyUseCase`).
- `src/infrastructure/`: Adapters for window management, screen capture, input control, rate limiting, and vision.
- `src/config/`: Configuration definitions and YAML loaders.
- `tests/`: Unit test suite covering geometry, Bézier calculations, rate limiting, and use case flows.

## Quick Start

```powershell
# Run unit tests
python -m unittest discover -s tests -v

# Run Flow A (Feed Commenting)
python main.py --flow a --config configs/settings.yaml

# Run Flow B (Thread Replying)
python main.py --flow b --config configs/settings.yaml
```
