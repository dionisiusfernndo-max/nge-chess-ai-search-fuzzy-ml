# Nge-Chess AI

Nge-Chess AI is a chess game application that integrates Search Methods, Fuzzy Expert System, and Machine Learning to create adaptive artificial intelligence behavior in a playable chess environment.

This project was developed for the **Machine Learning for Intelligent System** final project. The system demonstrates the implementation of Alpha-Beta Search, Fuzzy Expert System, Reinforcement Learning, Supervised Learning, and K-Means Clustering in a chess game.

## Features

* Player vs Player mode
* Easy mode using Reinforcement Learning
* Medium mode using Alpha-Beta Search with Machine Learning evaluation
* Hard mode using Enhanced Alpha-Beta Search, tactical evaluation, transposition table, and fuzzy-based search tuning
* Dynamic mode using Fuzzy Expert System to select the most suitable AI behavior
* Timer system for both players
* Move history panel
* Captured pieces display
* Legal chess move validation
* Checkmate, stalemate, repetition draw, castling, en passant, and pawn promotion support
* Fullscreen chess board interface using Pygame

## AI Methods

### 1. Search Method

Nge-Chess AI uses Alpha-Beta Pruning as an optimization of the Minimax algorithm. This method is used to evaluate possible chess moves and reduce unnecessary search branches during decision-making.

### 2. Fuzzy Expert System

The Fuzzy Expert System is used to generate a dynamic difficulty score based on several game conditions:

* Material balance
* Move count
* Remaining time

The fuzzy score is used in two ways:

* To adjust search parameters in Hard mode
* To select Easy, Medium, or Hard AI behavior in Dynamic mode

### 3. Machine Learning

This project applies three Machine Learning approaches:

* Reinforcement Learning for Easy mode
* Supervised Learning using MLPRegressor for board evaluation
* Unsupervised Learning using K-Means Clustering to detect game phases:

  * Opening
  * Middlegame
  * Endgame

## Game Modes

| Mode             | Method                                                              |
| ---------------- | ------------------------------------------------------------------- |
| Player vs Player | Human vs Human                                                      |
| Easy             | Reinforcement Learning                                              |
| Medium           | Alpha-Beta Search + Supervised Learning + K-Means                   |
| Hard             | Enhanced Alpha-Beta Search + Machine Learning + Fuzzy Search Tuning |
| Dynamic          | Fuzzy Expert System Controller                                      |

## Project Structure

```text
nge-chess-ai-search-fuzzy-ml/
├── ChessEngine.py
├── ChessMain.py
├── ChessSmartMoveFinder.py
├── model_rl.pkl
├── model_supervised.pkl
├── model_unsupervised.pkl
├── images/
│   ├── wp.png
│   ├── wR.png
│   ├── wN.png
│   ├── wB.png
│   ├── wQ.png
│   ├── wK.png
│   ├── bp.png
│   ├── bR.png
│   ├── bN.png
│   ├── bB.png
│   ├── bQ.png
│   └── bK.png
└── README.md
```

## Main Files

| File                      | Description                                                                                                         |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `ChessMain.py`            | Main program for running the chess game interface                                                                   |
| `ChessEngine.py`          | Handles chess rules, legal moves, move log, checkmate, stalemate, castling, en passant, and pawn promotion          |
| `ChessSmartMoveFinder.py` | Contains AI logic, Alpha-Beta Search, Fuzzy Expert System, Reinforcement Learning, Supervised Learning, and K-Means |
| `model_rl.pkl`            | Saved Reinforcement Learning model                                                                                  |
| `model_supervised.pkl`    | Saved Supervised Learning model                                                                                     |
| `model_unsupervised.pkl`  | Saved K-Means clustering model                                                                                      |
| `images/`                 | Folder containing chess piece images                                                                                |

## Requirements

Before running the application, install the required Python libraries:

```bash
pip install pygame numpy scikit-learn
```

## How to Run

Run the main program using:

```bash
python ChessMain.py
```

Make sure the `images` folder is located in the same directory as `ChessMain.py`.

## Keyboard Controls

| Key   | Function                      |
| ----- | ----------------------------- |
| `Z`   | Undo move                     |
| `R`   | Restart game                  |
| `M`   | Return to menu                |
| `Q`   | Quit game                     |
| `ESC` | Exit fullscreen or close game |

## Notes

* The `.pkl` files are trained model files used by the AI system.
* The `__pycache__` folder is automatically generated by Python and does not need to be uploaded.
* If the model files are deleted, the program can retrain the models when executed, but the initial run may take longer.
* The Hard and Dynamic modes may require more processing time because they use deeper search and AI evaluation.

## Author

Developed as a final project for Machine Learning for Intelligent System.

Group Members:

* Dionisius Fernando / 36240004
* Winson Gunawan Gotama / 36240005
* Calsen Arlu / 36240011
* Jeremy Matthew Santoso / 36240026
* Jason Adithya Putra Hariyanto / 36240027

## License

This project is developed for academic purposes.
