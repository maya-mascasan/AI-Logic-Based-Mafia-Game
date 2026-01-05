import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import os
import threading
import random

PROVER9_CMD = "/mnt/c/Users/mmasc/OneDrive - Technical University of Cluj-Napoca/Year 3/AI/LADR-2009-11A/bin/prover9"

def windows_to_wsl_path(path):
    path = os.path.abspath(path)
    drive = path[0].lower()
    rest = path[2:].replace("\\", "/")
    return f"/mnt/{drive}{rest}"

class MafiaGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Classic Mafia: Prover9 Edition")
        self.root.geometry("1000x850")

        self.day_count = 1
        self.phase = "SETUP"
        self.players = ["Serban", "Maya", "Vlad", "Mihai", "Raisa"]
        self.roles = {}
        self.status = {}
        self.player_name = "Serban"
        
        self.log_text = None
        self.action_frame = None
        self.target_var = tk.StringVar()
        
        self.setup_ui()
        self.start_game()

    def setup_ui(self):
        tk.Label(self.root, text="🕵️ Mafia Game Loop", font=("Helvetica", 18, "bold")).pack(pady=10)
        
        frame_log = tk.LabelFrame(self.root, text="Game Log", padx=10, pady=10)
        frame_log.pack(fill="both", expand=True, padx=10)
        
        self.log_text = tk.Text(frame_log, height=15, state="disabled", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

        self.status_frame = tk.LabelFrame(self.root, text="Living Players", padx=10, pady=5)
        self.status_frame.pack(fill="x", padx=10, pady=5)
        self.player_labels = {}

        self.action_frame = tk.LabelFrame(self.root, text="Your Action", padx=10, pady=10)
        self.action_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_instruction = tk.Label(self.action_frame, text="Waiting for game start...", font=("Arial", 12))
        self.lbl_instruction.pack(pady=5)
        
        self.combo_target = ttk.Combobox(self.action_frame, textvariable=self.target_var, state="disabled")
        self.combo_target.pack(pady=5)
        
        self.btn_action = tk.Button(
            self.action_frame,
            text="Confirm Action",
            command=self.handle_player_action,
            bg="#4CAF50",
            fg="white",
            state="disabled"
        )
        self.btn_action.pack(pady=5)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def update_status_board(self):
        for widget in self.status_frame.winfo_children():
            widget.destroy()
            
        for p in self.players:
            stat = self.status[p]
            role_reveal = f"({self.roles[p]})" if (p == self.player_name or stat == "Dead") else "(?)"
            color = "green" if stat == "Alive" else "red"
            font_style = ("Arial", 10, "bold") if p == self.player_name else ("Arial", 10)
            
            lbl = tk.Label(
                self.status_frame,
                text=f"{p}: {stat} {role_reveal}",
                fg=color,
                font=font_style
            )
            lbl.pack(side="left", padx=10)

    def start_game(self):
        self.log("=== NEW GAME STARTED ===")
        role_deck = ["Killer", "Doctor", "LadyCompanion", "Cop", "Villager"]
        random.shuffle(role_deck)
        
        for i, p in enumerate(self.players):
            self.roles[p] = role_deck[i]
            self.status[p] = "Alive"
        
        self.update_status_board()
        self.log(f"You are {self.player_name}. Your role is: {self.roles[self.player_name]}")
        
        if self.roles[self.player_name] == "Killer":
            self.log("MISSION: Kill everyone else.")
        else:
            self.log("MISSION: Find and lynch the Killer.")

        self.start_night_phase()

    def get_alive_players(self):
        return [p for p, s in self.status.items() if s == "Alive"]

    def start_night_phase(self):
        self.phase = "NIGHT"
        self.log(f"\n--- NIGHT {self.day_count} ---")
        
        alive = self.get_alive_players()
        if self.player_name not in alive:
            self.log("You are dead. You watch the night unfold...")
            self.root.after(2000, self.process_night_turn)
            return

        my_role = self.roles[self.player_name]
        targets = [p for p in alive if p != self.player_name]
        if my_role == "Doctor":
            targets = alive
        
        if my_role == "Villager":
            self.lbl_instruction.config(text="You are a Villager. Sleep tight.")
            self.combo_target.config(values=[], state="disabled")
            self.btn_action.config(text="Sleep", state="normal")
        else:
            self.lbl_instruction.config(text=f"Role: {my_role}. Choose target:")
            self.combo_target.config(values=targets, state="readonly")
            self.btn_action.config(text="Confirm Night Action", state="normal")

    def handle_player_action(self):
        if self.phase == "NIGHT":
            self.btn_action.config(state="disabled")
            self.process_night_turn(self.target_var.get())
        elif self.phase == "DAY":
            self.btn_action.config(state="disabled")
            self.process_day_vote(self.target_var.get())

    def process_night_turn(self, player_target="None"):
        night_actions = {}
        alive = self.get_alive_players()
        
        for p in alive:
            if p == self.player_name:
                night_actions[p] = player_target if self.roles[p] != "Villager" else "None"
                continue
                
            role = self.roles[p]
            others = [x for x in alive if x != p]
            
            if not others:
                night_actions[p] = "None"
                continue

            if role == "Killer":
                night_actions[p] = random.choice(others)
            elif role == "Doctor":
                night_actions[p] = p if random.random() < 0.2 else random.choice(others)
            elif role == "LadyCompanion":
                night_actions[p] = random.choice(others)
            elif role == "Cop":
                night_actions[p] = random.choice(others)
            else:
                night_actions[p] = "None"

        self.log("Night actions locked. Calculating Logic via Prover9...")
        self.night_data_package = (self.roles, night_actions)
        
        thread = threading.Thread(
            target=self.run_prover9_logic,
            args=(self.roles, night_actions)
        )
        thread.start()

    def run_prover9_logic(self, roles, actions):
        victim = self.python_heuristic_check(roles, actions)
        prover9_input = self.build_prover9_file(roles, actions, victim)
        
        in_file = "mafia_turn.in"
        with open(in_file, "w", newline="\n") as f:
            f.write(prover9_input)
            
        wsl_in = windows_to_wsl_path(in_file)
        cmd = f'wsl -d Ubuntu "{PROVER9_CMD}" -f "{wsl_in}"'
        
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            output, _ = proc.communicate()
            success = "THEOREM PROVED" in output
            self.root.after(
                0,
                lambda: self.resolve_night(victim, success, actions)
            )
        except Exception:
            self.root.after(
                0,
                lambda: messagebox.showerror("Error", "Prover9 Failed")
            )

    def resolve_night(self, victim, proven, actions):
        self.log(f"--- MORNING {self.day_count} ---")
        
        if self.roles[self.player_name] == "Cop" and self.status[self.player_name] == "Alive":
            target = actions.get(self.player_name)
            if target and target != "None":
                result = "MAFIA" if self.roles[target] == "Killer" else "INNOCENT"
                self.log(f"[COP INTEL]: You investigated {target}. Result: {result}")

        if proven and victim:
            self.log(f"Tragedy! {victim} was found dead.")
            self.status[victim] = "Dead"
        elif proven and not victim:
            self.log("A peaceful night. No one died.")
        else:
            self.log("Logic Error: Prover9 outcome uncertain. Game continues assuming no death.")

        self.update_status_board()
        
        if self.check_game_over():
            return
        
        self.start_day_phase()

    def start_day_phase(self):
        self.phase = "DAY"
        alive = self.get_alive_players()
        
        if self.player_name not in alive:
            self.log("You are dead. The others are voting...")
            self.root.after(3000, lambda: self.resolve_votes("Auto"))
            return

        self.lbl_instruction.config(text="Who looks suspicious? Cast your vote:")
        self.combo_target.config(values=["Skip"] + alive, state="readonly")
        self.btn_action.config(text="Vote to Lynch", state="normal")

    def process_day_vote(self, player_vote):
        self.log(f"You voted for: {player_vote}")
        self.resolve_votes(player_vote)

    def resolve_votes(self, human_vote):
        alive = self.get_alive_players()
        votes = {p: 0 for p in alive}
        votes["Skip"] = 0

        for p in alive:
            if p == self.player_name:
                if human_vote == "Auto":
                    candidates = [x for x in alive if x != p] + ["Skip"]
                    votes[random.choice(candidates)] += 1
                else:
                    if human_vote in votes:
                        votes[human_vote] += 1
            else:
                valid_targets = [x for x in alive if x != p] + ["Skip"]
                if self.roles[p] == "Killer":
                    non_mafia_targets = [
                        x for x in valid_targets
                        if x == "Skip" or self.roles[x] != "Killer"
                    ]
                    choice = random.choice(non_mafia_targets or valid_targets)
                else:
                    choice = random.choice(valid_targets)
                
                votes[choice] += 1
                self.log(f"{p} voted for {choice}")

        max_votes = 0
        candidate = None
        for target, count in votes.items():
            if count > max_votes:
                max_votes = count
                candidate = target
            elif count == max_votes:
                candidate = None

        if candidate and candidate != "Skip":
            self.log(f"The town has spoken. {candidate} is lynched!")
            self.status[candidate] = "Dead"
        else:
            self.log("Vote tied or skipped. No one lynched.")

        self.update_status_board()
        if not self.check_game_over():
            self.day_count += 1
            self.root.after(3000, self.start_night_phase)

    def check_game_over(self):
        alive = self.get_alive_players()
        mafia_count = sum(1 for p in alive if self.roles[p] == "Killer")
        villager_count = len(alive) - mafia_count

        if mafia_count == 0:
            messagebox.showinfo("Game Over", "TOWN WINS! The Killer is dead.")
            self.phase = "OVER"
            return True
        elif mafia_count >= villager_count:
            messagebox.showinfo("Game Over", "MAFIA WINS! They have taken over the town.")
            self.phase = "OVER"
            return True
        return False

    def python_heuristic_check(self, roles, actions):
        killer = next((p for p, r in roles.items() if r == "Killer"), None)
        doctor = next((p for p, r in roles.items() if r == "Doctor"), None)
        lady = next((p for p, r in roles.items() if r == "LadyCompanion"), None)

        targets = {p: actions.get(p, "None") for p in self.players}
        blocked_players = []
        if lady and targets[lady] != "None":
            blocked_players.append(targets[lady])

        protected_player = None
        if doctor and targets[doctor] != "None":
            if doctor not in blocked_players:
                protected_player = targets[doctor]

        victim = None
        if killer and targets[killer] != "None":
            target = targets[killer]
            if killer not in blocked_players:
                if target != protected_player:
                    victim = target
        return victim

    def build_prover9_file(self, roles, actions, expected_victim):
        lines = [
            "set(auto).",
            "assign(max_weight, 50).",
            "clear(predicate_elim).",
            "formulas(assumptions).",
            "  all y (Blocked(y) <-> (exists x (Role(x,LadyCompanion) & Target(x,y)))).",
            "  all y (Protected(y) <-> (exists x (Role(x,Doctor) & Target(x,y) & -Blocked(x)))).",
            "  all y (Dies(y) <-> (exists x (Role(x,Killer) & Target(x,y) & -Blocked(x) & -Protected(y)))).",
            "",
        ]

        names_lower = [n.lower() for n in self.players]
        for i in range(len(names_lower)):
            for j in range(i + 1, len(names_lower)):
                lines.append(f"  {names_lower[i]} != {names_lower[j]}.")

        role_types = ["Killer", "Doctor", "LadyCompanion", "Cop", "Villager"]
        for i in range(len(role_types)):
            for j in range(i + 1, len(role_types)):
                lines.append(f"  {role_types[i]} != {role_types[j]}.")

        lines.append("")
        role_clauses = [
            f"(x={p.lower()} & r={r})" for p, r in roles.items()
        ]
        full_role_def = " | ".join(role_clauses)
        lines.append(f"  all x all r (Role(x,r) <-> ({full_role_def})).")

        target_clauses = [
            f"(x={p.lower()} & y={t.lower()})"
            for p, t in actions.items()
            if t and t != "None"
        ]

        if target_clauses:
            lines.append(
                f"  all x all y (Target(x,y) <-> ({' | '.join(target_clauses)}))."
            )
        else:
            lines.append("  all x all y (Target(x,y) <-> $F).")

        lines.append("end_of_list.")
        lines.append("formulas(goals).")
        if expected_victim:
            lines.append(f"  Dies({expected_victim.lower()}).")
        else:
            lines.append("  all x -Dies(x).")
        lines.append("end_of_list.")
        
        return "\n".join(lines)

if __name__ == "__main__":
    root = tk.Tk()
    app = MafiaGame(root)
    root.mainloop()
