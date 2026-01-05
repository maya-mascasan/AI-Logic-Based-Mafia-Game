# AI Logic-Based Mafia Game (Prover9)

A formal implementation of the "Mafia" game where night-phase resolutions are determined using **First-Order Logic (FOL)** and the **Prover9 theorem prover**. Instead of procedural "if-else" statements, this engine uses symbolic reasoning to ensure that every death or saved action is formally verified against the game rules.

## 🧠 Logical Framework
The project models the game as a declarative system. Every night, the game generates a Prover9 input file containing assumptions (roles and targets) and the core game rules expressed as logical equivalences.

### Logical Predicates
* `Role(x, r)` – Player `x` has role `r`
* `Target(x, y)` – Player `x` targets player `y`
* `Blocked(y)` – Player `y` is blocked by a LadyCompanion
* `Protected(y)` – Player `y` is protected by a Doctor
* `Dies(y)` – Player `y` dies during the night phase

### Core Logic Rules (FOL)
- **Blocking:** A player is blocked if and only if the LadyCompanion targets them.
- **Protection:** A player is protected if the Doctor targets them and the Doctor is not blocked.
- **Death:** A player dies if the Killer targets them, the Killer is not blocked, and the target is not protected.

## 🛠 Technical Features
* **Symbolic Reasoning:** Uses Prover9 to handle complex interactions (e.g., LadyCompanion blocking a Doctor who was trying to save a Killer's target).
* **AI Behavior:** Multi-agent simulation with role-based AI for non-player characters (Killer, Doctor, Cop, etc.).
* **WSL Integration:** Implemented a path conversion utility to bridge Windows environments with WSL-based Prover9 execution.
* **Formal Correctness:** The night resolution is guaranteed to be formally correct, following strictly from the actual game state and declarative rules.

## 🚀 Why This Matters
This project demonstrates how symbolic logic can be integrated into interactive systems to ensure **explainability and correctness**. By using a theorem prover, the system scales effortlessly as new roles or complex interactions are added without the risk of procedural logic bugs.
