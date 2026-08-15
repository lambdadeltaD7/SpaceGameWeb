import random



def generate_world_dict(seed: int | None = None):
    seed = seed if seed is not None else random.randint(0, 1_000_000_000)
    random.seed(seed)

    w = random.randint(16, 64)
    h = random.randint(16, 64)

    world = {
        "seed": seed,
        "w": w,
        "h": h
    }

    cnt_planets = random.randint(2, 16)
    planets = []

    for _ in range(cnt_planets):
        planets.append({
            "res1": random.randint(10, 100),
            "res2": random.randint(10, 100),
            "x": random.randint(0, w - 1),
            "y": random.randint(0, h - 1)
        })
    
    return world, planets


