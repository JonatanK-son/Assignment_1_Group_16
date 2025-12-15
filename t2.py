import mesa
from mesa import Agent, Model
from mesa.space import MultiGrid
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- Data Structures ---
class Task:
    def __init__(self, id, duration, resources):
        self.id = id
        self.duration = duration
        self.resources = resources
        self.assigned_agents = []
        self.completed = False

class WorkerAgent(Agent):
    def __init__(self, model, capacity, unique_id):
        super().__init__(model)
        self.custom_id = unique_id 
        self.capacity = capacity
        self.current_tasks = [] 
        self.color = "grey" # For viz

    def step(self):
        pass # Logic handled by model

class CooperativeModel(Model):
    def __init__(self):
        super().__init__()
        self.grid = MultiGrid(5, 5, False) # Small grid just for visualization
        self.tasks = []
        self.step_count = 0
        
        # 1. Create Tasks (50)
        for i in range(50):
            # Example logic: mix of resource needs
            res = self.random.choice([1, 2, 3])
            dur = self.random.randint(5, 20)
            self.tasks.append(Task(i, dur, res))

        # 2. Create Agents (Fixed on Grid)
        configs = [(2, "Agent 1", (1, 2)), (1, "Agent 2", (2, 2)), (2, "Agent 3", (3, 2))]
        self.workers = []
        
        for cap, name, pos in configs:
            a = WorkerAgent(self, cap, name)
            self.grid.place_agent(a, pos)
            self.workers.append(a)

    def step(self):
        self.step_count += 1
        print(f'{{"type":"get_step","step":{self.step_count}}}')

        # --- Allocation ---
        pending = [t for t in self.tasks if not t.completed and len(t.assigned_agents) < t.resources]
        
        for task in pending:
            needed = task.resources - len(task.assigned_agents)
            # Find capable agents
            candidates = [a for a in self.workers if len(a.current_tasks) < a.capacity and a not in task.assigned_agents]
            
            if len(candidates) >= needed:
                for i in range(needed):
                    candidates[i].current_tasks.append(task)
                    task.assigned_agents.append(candidates[i])

        # --- Execution & Printing ---
        active_task_ids = []
        
        for agent in self.workers:
            agent.color = "grey" # Reset color
            if not agent.current_tasks:
                continue

            # Check for cooperation (is anyone else working on my tasks?)
            is_cooperating = False
            for t in agent.current_tasks:
                if t.resources > 1:
                    is_cooperating = True
                print(f"{agent.custom_id} is working on Task {t.id}, Task Duration: {t.duration}")

                # Decrement Duration (Only once per task)
                if agent == t.assigned_agents[0]:
                    t.duration -= 1
                if t.duration <= 0:
                    t.completed = True
            
            # Update Viz Color
            agent.color = "magenta" if is_cooperating else "cyan"
            
            # Clean completed
            agent.current_tasks = [t for t in agent.current_tasks if not t.completed]

def run_viz():
    model = CooperativeModel()
    fig, ax = plt.subplots(figsize=(5,5))

    def update(frame):
        model.step()
        ax.clear()
        
        # Draw Agents
        for agent in model.workers:
            ax.scatter(agent.pos[0], agent.pos[1], c=agent.color, s=500, label=agent.custom_id)
            ax.text(agent.pos[0], agent.pos[1], f"{agent.custom_id}\nCap:{agent.capacity}", 
                    ha='center', va='center', color='white', fontweight='bold')
        
        ax.set_xlim(0, 5)
        ax.set_ylim(0, 5)
        ax.set_title(f"Step {frame} (Magenta=Coop, Cyan=Solo)")
        ax.axis('off')

    anim = FuncAnimation(fig, update, frames=15, repeat=False)
    plt.show()

if __name__ == "__main__":
    run_viz()