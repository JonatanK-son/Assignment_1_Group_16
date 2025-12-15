import mesa
import random
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

class WorkerAgent(mesa.Agent):
    def __init__(self, model, capacity, unique_id):
        super().__init__(model)
        self.custom_id = unique_id 
        self.capacity = capacity
        self.current_tasks = [] 
        self.color = "grey" # Default: Idle

    def step(self):
        pass # Logic is handled centrally by the model for this specific scheduling task

class CooperativeModel(mesa.Model):
    def __init__(self):
        super().__init__()
        # Grid: 5x5 for simple visualization
        self.grid = mesa.space.MultiGrid(5, 5, False) 
        self.tasks = []
        self.step_count = 0
        
        # 1. Create Tasks (50 tasks with random requirements)
        for i in range(50):
            res = self.random.choice([1, 2, 3]) 
            dur = self.random.randint(5, 20)    
            self.tasks.append(Task(i, dur, res))

        configs = [
            (2, "Agent 1", (1, 2)), 
            (1, "Agent 2", (2, 2)), 
            (2, "Agent 3", (3, 2))
        ]
        
        self.workers = []
        for cap, name, pos in configs:
            a = WorkerAgent(self, cap, name)
            self.grid.place_agent(a, pos)
            self.workers.append(a)

    def step(self):
        self.step_count += 1
        # Required Print Format
        print(f'{{"type":"get_step","step":{self.step_count}}}')

        pending = [t for t in self.tasks if not t.completed and len(t.assigned_agents) < t.resources]
        
        for task in pending:
            needed = task.resources - len(task.assigned_agents)
            
            candidates = [a for a in self.workers 
                          if len(a.current_tasks) < a.capacity 
                          and a not in task.assigned_agents]
            
            if len(candidates) >= needed:
                for i in range(needed):
                    agent = candidates[i]
                    agent.current_tasks.append(task)
                    task.assigned_agents.append(agent)

        for agent in self.workers:
            agent.color = "grey" 
            
            if not agent.current_tasks:
                continue

            # Determine Agent Status
            is_cooperating = False
            task_ids = []
            
            for t in agent.current_tasks:
                task_ids.append(str(t.id))
                
                # Check for cooperation (is the task needing > 1 person?)
                if t.resources > 1:
                    is_cooperating = True
                
                # Print Status
                print(f"{agent.custom_id} is working on Task {t.id}, Task Duration: {t.duration}")

                # Decrement Duration (Only once per task, by the 'primary' agent)
                if agent == t.assigned_agents[0]:
                    t.duration -= 1
                
                # Check Completion
                if t.duration <= 0:
                    t.completed = True
            
            # Set Color based on status
            agent.color = "magenta" if is_cooperating else "cyan"
            
            # Cleanup completed tasks from agent's list
            agent.current_tasks = [t for t in agent.current_tasks if not t.completed]

# --- Visualization Function ---
def run_viz():
    model = CooperativeModel()
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    def update(frame):
        model.step()
        ax.clear()
        
        x_vals = []
        y_vals = []
        colors = []
        labels = []
        
        for agent in model.workers:
            x_vals.append(agent.pos[0])
            y_vals.append(agent.pos[1])
            colors.append(agent.color)
            
            task_list = [str(t.id) for t in agent.current_tasks]
            if not task_list:
                status_text = "Idle"
            else:
                status_text = f"T:{','.join(task_list)}"
            labels.append(f"{agent.custom_id}\n(Cap {agent.capacity})\n{status_text}")

        
        ax.scatter(x_vals, y_vals, c=colors, s=1500, edgecolors='black', alpha=0.8)
        
        for i in range(len(model.workers)):
            ax.text(x_vals[i], y_vals[i], labels[i], 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='black')

        ax.set_xlim(0, 4)
        ax.set_ylim(0, 4)
        ax.set_title(f"Step {frame} | Cyan=Solo, Magenta=Coop", fontsize=12)
        ax.axis('off') #

    anim = FuncAnimation(fig, update, frames=20, repeat=False, interval=1000)
    plt.show()

if __name__ == "__main__":
    run_viz()