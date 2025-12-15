import mesa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- Configuration ---
NUM_CARS = 10
NUM_SPOTS = 5
GRID_SIZE = 10
MAX_STEPS = 101

class ParkingAgent(mesa.Agent):
    """A parking spot. Green if free, Covered if occupied."""
    def __init__(self, model):
        super().__init__(model)
        self.occupied = False

class CarAgent(mesa.Agent):
    """A car. Blue if searching, Red if parked."""
    def __init__(self, model):
        super().__init__(model)
        self.parked = False
        self.parking_duration = 0
        self.steps_searching = 0

    def try_to_park(self):
        """Checks current cell for a free spot and parks if possible."""
        # 1. Get contents of current cell
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        
        # 2. Find a free parking spot
        parking_spot = next((obj for obj in cell_contents 
                             if isinstance(obj, ParkingAgent) and not obj.occupied), None)
   
        if parking_spot:
            self.parked = True
            parking_spot.occupied = True
            self.parking_duration = self.random.randint(3, 5)
            # Log successful search
            self.model.log_search_time(self.steps_searching)
            self.steps_searching = 0
            return True
        return False
   
    def move(self):
        # 1. Move randomly
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)
        self.steps_searching += 1
        
        # 2. OPTIMIZATION: Check for parking immediately after arriving
        self.try_to_park()
   
    def step(self):
        if self.parked:
            if self.parking_duration > 0:
                self.parking_duration -= 1
            else:
                # Leave parking
                self.parked = False
                # Free the spot at current location
                cell_contents = self.model.grid.get_cell_list_contents([self.pos])
                for obj in cell_contents:
                    if isinstance(obj, ParkingAgent):
                        obj.occupied = False
                
                # Move away immediately so we don't re-park instantly
                self.move()
        else:
            # If not parked, check if we are currently on a spot (e.g. spawned there)
            if not self.try_to_park():
                # If cannot park, move
                self.move()

class ParkingModel(mesa.Model):
    def __init__(self, N_cars=NUM_CARS, N_spots=NUM_SPOTS, width=GRID_SIZE, height=GRID_SIZE, seed=None):
        super().__init__(seed=seed)
        # OPTIMIZATION: torus=False (Parking lots have walls)
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.search_times = []

        # 1. Create Parking Spots
        for _ in range(N_spots):
            a = ParkingAgent(self)
            # Random placement retry loop
            while True:
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                # Only place if no other AGENT (spot or car) is there yet
                if self.grid.is_cell_empty((x,y)): 
                    self.grid.place_agent(a, (x, y))
                    break

        # 2. Create Cars
        for _ in range(N_cars):
            a = CarAgent(self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        self.datacollector = mesa.datacollection.DataCollector(
            model_reporters={"AvgSearchSteps": lambda m: np.mean(m.search_times) if m.search_times else 0}
        )

    def log_search_time(self, steps):
        self.search_times.append(steps)

    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle().do("step")

# --- Visualization Logic ---
def run_simulation():
    model = ParkingModel()
    
    # Setup Plot
    fig, ax = plt.subplots(figsize=(6,6))
    
    def update(frame):
        model.step()
        ax.clear()
        
        # Extract coordinates for plotting
        park_x, park_y = [], []
        car_moving_x, car_moving_y = [], []
        car_parked_x, car_parked_y = [], []
        
        for agent in model.agents:
            if isinstance(agent, ParkingAgent):
                park_x.append(agent.pos[0])
                park_y.append(agent.pos[1])
            elif isinstance(agent, CarAgent):
                if agent.parked:
                    car_parked_x.append(agent.pos[0])
                    car_parked_y.append(agent.pos[1])
                else:
                    car_moving_x.append(agent.pos[0])
                    car_moving_y.append(agent.pos[1])

        # Plot
        ax.scatter(park_x, park_y, c='green', s=200, marker='s', label='Empty Spot', alpha=0.3)
        ax.scatter(car_moving_x, car_moving_y, c='blue', s=100, label='Searching Car')
        ax.scatter(car_parked_x, car_parked_y, c='red', s=100, label='Parked Car')
        
        ax.set_xlim(-1, GRID_SIZE)
        ax.set_ylim(-1, GRID_SIZE)
        ax.set_title(f"Step: {frame} | Avg Search Steps: {np.mean(model.search_times) if model.search_times else 0:.1f}")
        ax.grid(True)
        if frame == 0: ax.legend(loc='upper right')

    anim = FuncAnimation(fig, update, frames=MAX_STEPS, repeat=False)
    plt.show()
    
    # Print Reflection Data
    print(f"Simulation ended. Average steps to find parking: {np.mean(model.search_times):.2f}")

if __name__ == "__main__":
    run_simulation()