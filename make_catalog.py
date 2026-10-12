"""Create the sample catalog: data/parts.csv with 20,000 engine spare parts.

Run:  python make_catalog.py

The parts are made up. Each one is a combination of a part name, a variant,
an engine size and an application, with an invented part number and price.
"""

import csv
import random
from itertools import product
from pathlib import Path

OUTPUT = Path(__file__).parent / "data" / "parts.csv"
HOW_MANY = 20_000

# category -> (lowest price, highest price in rupees, part names)
CATEGORIES = {
    "Filtration": (350, 2_800, [
        "Fuel Filter", "Oil Filter", "Air Filter", "Coolant Filter", "Fuel Water Separator",
        "Hydraulic Filter", "Crankcase Breather Filter", "Filter Head", "Filter Housing",
    ]),
    "Fuel System": (900, 48_000, [
        "Fuel Injector", "Fuel Pump", "Fuel Lift Pump", "Injector Nozzle", "Fuel Rail",
        "Fuel Pressure Regulator", "Fuel Pressure Sensor", "Fuel Shutoff Valve", "Fuel Line",
        "Fuel Tank Cap", "Injector Seal",
    ]),
    "Air Handling": (1_500, 95_000, [
        "Turbocharger", "Turbocharger Actuator", "Intercooler", "Intake Manifold", "Intake Hose",
        "Boost Pressure Sensor", "Air Compressor", "Throttle Valve", "Wastegate Valve",
    ]),
    "Cooling": (250, 32_000, [
        "Water Pump", "Thermostat", "Radiator", "Radiator Hose", "Radiator Cap", "Fan Belt",
        "Fan Clutch", "Cooling Fan", "Coolant Temperature Sensor", "Coolant Level Sensor",
        "Belt Tensioner", "Expansion Tank",
    ]),
    "Lubrication": (150, 21_000, [
        "Oil Pump", "Oil Cooler", "Oil Pressure Sensor", "Oil Pan", "Oil Pan Gasket",
        "Oil Dipstick", "Oil Filler Cap", "Oil Drain Plug", "Oil Seal",
    ]),
    "Engine Core": (400, 160_000, [
        "Piston", "Piston Ring Set", "Piston Pin", "Connecting Rod", "Connecting Rod Bearing",
        "Crankshaft", "Crankshaft Seal", "Camshaft", "Camshaft Bearing", "Cylinder Head",
        "Cylinder Liner", "Cylinder Head Gasket", "Main Bearing Set", "Intake Valve",
        "Exhaust Valve", "Valve Spring", "Valve Cover Gasket", "Rocker Arm", "Push Rod",
        "Timing Gear", "Flywheel", "Vibration Damper", "Engine Mount",
    ]),
    "Electrical": (200, 38_000, [
        "Alternator", "Starter Motor", "Glow Plug", "Wiring Harness", "Battery Cable",
        "Speed Sensor", "Crankshaft Position Sensor", "Camshaft Position Sensor",
        "Control Module", "Relay", "Fuse Box",
    ]),
    "Exhaust": (300, 120_000, [
        "Exhaust Manifold", "Exhaust Gasket", "Exhaust Pipe", "Muffler", "Exhaust Clamp",
        "Particulate Filter", "Oxidation Catalyst", "Urea Injector", "Nitrogen Oxide Sensor",
        "Exhaust Temperature Sensor", "Exhaust Gas Recirculation Valve",
        "Exhaust Gas Recirculation Cooler",
    ]),
    "Hardware": (60, 6_500, [
        "Hose Clamp", "Mounting Bracket", "Gasket Set", "Seal Kit", "Bolt Set", "Drive Belt",
        "Pulley", "Bearing",
    ]),
}

VARIANTS = ["", "Kit", "Assembly", "Heavy Duty", "Standard Duty", "Service Pack", "Remanufactured", "Premium"]
ENGINES = ["2.8 L", "3.9 L", "4.5 L", "5.9 L", "6.7 L", "8.9 L", "12 L", "15 L"]
APPLICATIONS = ["Truck", "Bus", "Generator", "Excavator", "Tractor", "Marine"]


def main() -> None:
    random.seed(7)  # the same catalog every time

    names = [(category, name) for category, (_, _, names) in CATEGORIES.items() for name in names]
    combinations = list(product(names, VARIANTS, ENGINES, APPLICATIONS))
    chosen = random.sample(combinations, HOW_MANY)

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["number", "name", "category", "engine", "application", "price", "stock"])
        for position, ((category, name), variant, engine, application) in enumerate(chosen):
            lowest, highest, _ = CATEGORIES[category]
            price = round(random.uniform(lowest, highest), -1)
            stock = 0 if random.random() < 0.12 else random.randint(1, 240)
            writer.writerow([
                f"PF-{100000 + position}",
                f"{name} {variant}".strip(),
                category,
                engine,
                application,
                int(price),
                stock,
            ])
    print(f"Wrote {HOW_MANY} parts to {OUTPUT.name} ({len(combinations)} combinations were possible).")


if __name__ == "__main__":
    main()
