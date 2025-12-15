import mesa
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd

# --- 1. Agent Definitions ---

class ParkingSpace(mesa.Agent):
    """
    A specific grid cell representing a parking spot.
    """
    def __init__(self, model):
        super().__init__(model)
        self.type_label = "Space"
        self.occupied = False

    def step(self):
        # Parking spaces are static; they don't perform actions.
        pass

class Car(mesa.Agent):
    """
    A car that moves effectively randomly to find a spot.
    """
    def __init__(self, model):
        super().__init__(model)
        self.type_label = "Car"
        self.state = "DRIVING" # States: DRIVING, PARKED
        self.steps_searching = 0
        self.park_timer = 0
        self.park_duration = 0

    def move(self):
        # Pick a random neighboring cell to move to
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True, # Include diagonals
            include_center=False
        )
        if possible_steps:
            new_position = self.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)

    def try_park(self):
        # Check agents in the current cell
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        
        for agent in cell_contents:
            if isinstance(agent, ParkingSpace):
                if not agent.occupied:
                    # Park here
                    agent.occupied = True
                    self.state = "PARKED"
                    # Req 5: Stay for 3 to 5 steps
                    self.park_duration = random.randint(3, 5)
                    self.park_timer = 0
                    return True
        return False

    def step(self):
        if self.state == "DRIVING":
            self.move()
            self.steps_searching += 1
            self.try_park()
            
        elif self.state == "PARKED":
            self.park_timer += 1
            # Req 5: Leave after specific steps
            if self.park_timer >= self.park_duration:
                # Leave the spot
                self.state = "DRIVING"
                self.steps_searching = 0 # Reset search counter for next attempt
                
                # Free the parking space agent in this cell
                cell_contents = self.model.grid.get_cell_list_contents([self.pos])
                for agent in cell_contents:
                    if isinstance(agent, ParkingSpace):
                        agent.occupied = False
                
                # Move away immediately so we don't instantly re-park
                self.move()

# --- 2. Model Definition ---

class ParkingLotModel(mesa.Model):
    """
    A model with some number of cars and parking spaces.
    """
    def __init__(self, N_cars, N_spaces, width=10, height=10):
        super().__init__()
        self.num_cars = N_cars
        self.num_spaces = N_spaces
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.running = True

        # Req 6: Data Collector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Average Search Steps": compute_avg_search
            },
            agent_reporters={
                "State": lambda a: a.state if isinstance(a, Car) else "N/A",
                "SearchSteps": lambda a: a.steps_searching if isinstance(a, Car) else None
            }
        )

        # Create Parking Spaces (Randomly placed, but distinct)
        # We ensure spaces don't overlap on initialization
        all_coords = [(x, y) for x in range(width) for y in range(height)]
        chosen_coords = random.sample(all_coords, self.num_spaces)

        for coord in chosen_coords:
            space = ParkingSpace(self)
            self.grid.place_agent(space, coord)
            # Note: In Mesa 3.0, agent is automatically added to self.agents when created with (self)

        # Create Cars (Req 1: At least 10)
        for _ in range(self.num_cars):
            car = Car(self)
            
            # Place car at random empty location (or just random)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(car, (x, y))

    def step(self):
        self.datacollector.collect(self)
        # Mesa 3.0 Scheduling: explicit shuffle_do on the agents collection
        self.agents.shuffle_do("step")

# Helper function for data collection
def compute_avg_search(model):
    # In Mesa 3.0, model.agents is an AgentSet containing all agents
    cars_searching = [
        a.steps_searching 
        for a in model.agents 
        if isinstance(a, Car) and a.state == "DRIVING"
    ]
    if cars_searching:
        return sum(cars_searching) / len(cars_searching)
    return 0

# --- 3. Visualization and Execution ---

def run_simulation(n_cars, n_spaces, steps=50):
    print(f"--- Running Simulation: {n_cars} Cars, {n_spaces} Spaces ---")
    model = ParkingLotModel(N_cars=n_cars, N_spaces=n_spaces, width=10, height=10)
    
    # Run for a set number of steps
    for i in range(steps):
        model.step()
        
    # Req 6 & 7: Displaying Data
    data = model.datacollector.get_model_vars_dataframe()
    
    # Plotting
    plt.figure(figsize=(10, 4))
    plt.plot(data["Average Search Steps"])
    plt.title(f"Average Steps Spent Searching (Cars={n_cars}, Spaces={n_spaces})")
    plt.xlabel("Simulation Step")
    plt.ylabel("Avg Steps")
    plt.show()
    
    return data

# --- Run Scenarios (Req 8) ---

# Scenario A: Standard (Traffic > Spaces)
if __name__ == "__main__":
    run_simulation(n_cars=10, n_spaces=5)
    run_simulation(n_cars=5, n_spaces=10)

    # --- Graphical Grid Visualization (Matplotlib Animation) ---
    def visualize_grid(model):
        """
        Helper to visualize the grid state.
        0 = Empty Road (Purple)
        1 = Empty Parking Space (Green)
        2 = Car Driving (Yellow)
        3 = Car Parked (Red)
        """
        grid_data = np.zeros((model.grid.width, model.grid.height))
        
        # Fill grid data
        for agent in model.agents:
            x, y = agent.pos
            if isinstance(agent, ParkingSpace):
                if not agent.occupied:
                    grid_data[x][y] = 1 # Green spot (Empty Space)
                else:
                    grid_data[x][y] = 3 # Red spot (Parked Car)
            elif isinstance(agent, Car):
                if agent.state == "DRIVING":
                     # If there is a parking space here, don't overwrite it visually
                     # unless we want to show the car passing over.
                     # For simplicity, 2 = Car
                     grid_data[x][y] = 2

        return grid_data

    fig, ax = plt.subplots(figsize=(5,5))
    model_viz = ParkingLotModel(N_cars=15, N_spaces=5, width=10, height=10)

    def update(frame):
        model_viz.step()
        grid_matrix = visualize_grid(model_viz)
        ax.clear()
        # 0=Purple (Empty), 1=Green (Space), 2=Yellow (Car), 3=Red (Parked)
        ax.imshow(grid_matrix, cmap='viridis', vmin=0, vmax=3)
        ax.set_title(f"Step: {frame}")
        ax.axis('off')

    print("Generating Animation...")
    ani = animation.FuncAnimation(fig, update, frames=30, interval=200)
    plt.show()