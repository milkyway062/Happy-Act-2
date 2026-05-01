class SharedState:
    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.paused = False
        self.win = False
        self.loss = False
        self.wins = 0
        self.losses = 0
        self.runtime = 0


# global default
_game_states = {"default": SharedState("default")}


def get_state(name="default"):
    return _game_states[name]


def add_game_state(name):
    if name in _game_states:
        raise ValueError(f"State '{name}' already exists")
    _game_states[name] = SharedState()
    return _game_states[name]


def remove_game_state(name):
    if name == "default":
        raise ValueError("Cannot remove default state")
    del _game_states[name]


def update_state(name="default", **kwargs):
    state = get_state(name)
    for key, value in kwargs.items():
        if hasattr(state, key):
            setattr(state, key, value)
            print(f"Updated state '{name}': {key} = {value}")
        else:
            raise ValueError(f"State has no attribute '{key}'")
