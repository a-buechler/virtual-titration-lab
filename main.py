from dataclasses import dataclass
import random
import math
import matplotlib.pyplot as plt
from drafter import *


@dataclass
class Titrant:
    """Store information about the titrant being added."""
    identity: str
    concentration: float
    volume_added: float


@dataclass
class Flask:
    """Store information about the solution being titrated."""
    identity: str
    concentration: float
    volume: float
    is_pink: bool
    titrant_added: Titrant


@dataclass
class State:
    """Store the current experiment and its progress."""
    flask: Flask
    history: list[Flask]
    increment: float
    volume_unit: str
    concentration_unit: str
    status: str


def make_initial_state() -> State:
    """Create the initial state for the website."""
    titrant = Titrant("NaOH", 0.1, 0.0)
    flask = Flask("HCl", 0.1, 25.0, False, titrant)

    return State(
        flask,
        [],
        1.0,
        "mL",
        "M",
        "home"
    )

def convert_volume_to_ml(volume: float, unit: str) -> float:
    """Convert the supplied volume into milliliters."""
    if unit == "L":
        return volume * 1000

    return volume


def convert_concentration_to_molarity(
    concentration: float, unit: str
) -> float:
    """Convert the supplied concentration into molarity."""
    if unit == "mM":
        return concentration / 1000

    return concentration


def increment_options(unit: str) -> list[str]:
    """Return appropriate titrant increments for the selected unit."""
    if unit == "L":
        return ["0.0001", "0.0005", "0.001", "0.002", "0.005"]

    return ["0.1", "0.5", "1.0", "2.0", "5.0"]


def equivalence_volume(flask: Flask) -> float:
    """Calculate the volume needed to reach the equivalence point."""
    acid_moles = flask.concentration * flask.volume / 1000

    return (
        acid_moles / flask.titrant_added.concentration * 1000
    )


def add_volume(current_volume: float, amount: float) -> float:
    """Add the new titrant volume using the sum loop pattern."""
    new_volume = 0.0

    for volume in [current_volume, amount]:
        new_volume += volume

    return new_volume


def copy_flask(flask: Flask) -> Flask:
    """Create an independent snapshot of the current flask."""
    titrant_copy = Titrant(
        flask.titrant_added.identity,
        flask.titrant_added.concentration,
        flask.titrant_added.volume_added
    )

    return Flask(
        flask.identity,
        flask.concentration,
        flask.volume,
        flask.is_pink,
        titrant_copy
    )


def calculate_ph(flask: Flask, volume_added: float) -> float:
    """Estimate pH for a strong acid and strong base titration."""
    acid_moles = (
        flask.concentration * flask.volume / 1000
    )

    base_moles = (
        flask.titrant_added.concentration * volume_added / 1000
    )

    total_liters = (
        flask.volume + volume_added
    ) / 1000

    if acid_moles > base_moles:
        hydrogen = (
            acid_moles - base_moles
        ) / total_liters

        return -math.log10(hydrogen)

    elif base_moles > acid_moles:
        hydroxide = (
            base_moles - acid_moles
        ) / total_liters

        return 14 + math.log10(hydroxide)

    else:
        return 7.0


def flask_color(flask: Flask) -> str:
    """Determine the indicator color based on titration progress."""
    if not flask.is_pink:
        return "white"

    if (
        flask.titrant_added.volume_added
        <= equivalence_volume(flask)
    ):
        return "lightpink"

    return "fuchsia"


def make_titration_graph(
    flask: Flask, history: list[Flask]
) -> None:
    """Create a pH graph and mark the equivalence volume."""
    volumes = [0.0]
    ph_values = [calculate_ph(flask, 0.0)]

    for snapshot in history:
        volume = snapshot.titrant_added.volume_added
        volumes.append(volume)

        ph_values.append(
            calculate_ph(flask, volume)
        )

    endpoint = equivalence_volume(flask)

    plt.figure()
    plt.plot(volumes, ph_values, marker="o")
    plt.axvline(endpoint, linestyle="--")
    plt.xlabel("Titrant added (mL)")
    plt.ylabel("Estimated pH")
    plt.title("Acid-Base Titration Curve")
    plt.ylim(0, 14)
    
@route
def home(state: State) -> Page:
    """Display the home page and experiment setup form."""
    return Page(state, [
        Header("Virtual Titration Lab"),
        Text("Welcome to the Virtual Titration Lab!"),
        Text(
            "Practice acid-base titrations and discover "
            "how to calculate an unknown concentration."
        ),

        Header("Experiment Setup", 2),

        Text("Volume of solution in the flask:"),
        TextBox("solution_volume", "25"),

        Text("Volume unit:"),
        SelectBox("volume_unit", ["mL", "L"], "mL"),

        Text("Titrant concentration unit:"),
        SelectBox("concentration_unit", ["M", "mM"], "M"),

        Text("Acid in the flask:"),
        SelectBox("flask_chemical", ["HCl", "HNO3"], "HCl"),

        Text("Base used as the titrant:"),
        SelectBox("titrant_chemical", ["NaOH", "KOH"], "NaOH"),

        Text("Titrant concentration:"),
        TextBox("titrant_concentration", "0.1"),

        Button("Start Titration", "start_titration")
    ])

@route
def index(state: State) -> Page:
    """Display the initial home page."""
    return home(state)

@route
def start_titration(
    state: State,
    solution_volume: float,
    volume_unit: str,
    concentration_unit: str,
    flask_chemical: str,
    titrant_chemical: str,
    titrant_concentration: float
) -> Page:
    """Convert measurements, randomize the acid, and begin."""
    volume_ml = convert_volume_to_ml(
        solution_volume, volume_unit
    )

    titrant_molarity = convert_concentration_to_molarity(
        titrant_concentration, concentration_unit
    )

    if volume_ml <= 0 or titrant_molarity <= 0:
        return Page(state, [
            Header("Invalid measurements"),
            Text("Volume and concentration must be positive."),
            Button("Return to setup", "home")
        ])

    # The actual acid concentration remains hidden until calculations.
    unknown_concentration = random.uniform(0.05, 0.20)

    titrant = Titrant(
        titrant_chemical,
        titrant_molarity,
        0.0
    )

    flask = Flask(
        flask_chemical,
        unknown_concentration,
        volume_ml,
        False,
        titrant
    )

    new_state = State(
        flask,
        [copy_flask(flask)],
        1.0 if volume_unit == "mL" else 0.001,
        volume_unit,
        concentration_unit,
        "in_progress"
    )

    return Page(new_state, [
        Header("Titration in Progress"),
        Text("Your flask is currently clear."),
        Text("Select how much titrant to add each time."),

        SelectBox(
            "increment",
            increment_options(volume_unit),
            str(new_state.increment)
        ),

        Button("Add Titrant", "continue_titrating"),

        Header("Your Flask", 2),

        Div(
            Text("Indicator solution"),
            style_background_color="white",
            style_padding="45px"
        ),

        Text(
            "The actual acid concentration will be revealed "
            "after the experiment."
        ),

        Button("Start Over", "start_over")
    ])

@route
def equivalence_reached(state: State) -> Page:
    """Display the pale pink equivalence point page."""
    return Page(state, [
        Header("Equivalence Point Reached!"),

        Text(
            "Congratulations! You have reached the "
            "equivalence point."
        ),

        Div(
            Header("Your Flask"),
            Text("The solution has turned pale pink."),
            style_background_color="lightpink",
            style_padding="45px"
        ),

        Text("What would you like to do next?"),

        Button(
            "Continue Titrating",
            "continue_titrating",
            [Argument("increment", state.increment)]
        ),

        Button(
            "See Calculations and Graph",
            "see_calculations"
        )
    ])


@route
def continue_titrating(
    state: State, increment: float
) -> Page:
    """Add titrant, record the volume, and check the endpoint."""
    flask = state.flask

    # Convert the selected increment into milliliters.
    amount_ml = convert_volume_to_ml(
        increment, state.volume_unit
    )

    endpoint_volume = equivalence_volume(flask)

    old_volume = flask.titrant_added.volume_added

    new_volume = add_volume(old_volume, amount_ml)

    # If this addition reaches the endpoint, record the exact
    # equivalence volume rather than the excess amount.
    if not flask.is_pink and new_volume >= endpoint_volume:
        flask.titrant_added.volume_added = endpoint_volume
        flask.is_pink = True

        state.increment = increment
        state.status = "equivalence"
        state.history.append(copy_flask(flask))

        return equivalence_reached(state)

    flask.titrant_added.volume_added = new_volume

    state.increment = increment
    state.history.append(copy_flask(flask))

    # The user has already reached the endpoint.
    if flask.is_pink:
        state.status = "overshot"

        return Page(state, [
            Header("You Have Overshot!"),

            Text(
                "You have added excess titrant. "
                "The solution is now bright fuchsia."
            ),

            Div(
                Header("Your Flask"),
                Text("Excess titrant present"),
                style_background_color="fuchsia",
                style_padding="45px"
            ),

            Text(
                "You can continue adding titrant or "
                "view your calculations."
            ),

            SelectBox(
                "increment",
                increment_options(state.volume_unit),
                str(increment)
            ),

            Button("Add More Titrant", "continue_titrating"),

            Button(
                "See Calculations and Graph",
                "see_calculations"
            )
        ])

    # The endpoint has not been reached yet.
    state.status = "in_progress"

    return Page(state, [
        Header("Titration in Progress"),

        Text("The solution is still clear."),

        Text(
            "Total titrant added: "
            + str(round(new_volume, 2))
            + " mL"
        ),

        SelectBox(
            "increment",
            increment_options(state.volume_unit),
            str(increment)
        ),

        Button("Add Titrant", "continue_titrating"),

        Div(
            Header("Your Flask"),
            Text("Indicator solution"),
            style_background_color=flask_color(flask),
            style_padding="45px"
        )
    ])

@route
def see_calculations(state: State) -> Page:
    """Display the titration graph and concentration calculations."""
    flask = state.flask

    titrant_volume = flask.titrant_added.volume_added

    titrant_moles = (
        flask.titrant_added.concentration
        * titrant_volume / 1000
    )

    calculated_concentration = (
        titrant_moles / (flask.volume / 1000)
    )

    make_titration_graph(flask, state.history)

    return Page(state, [
        Header("Calculations and Graph"),

        Header("Experimental Results", 2),

        Text(
            "Volume of titrant used: "
            + str(round(titrant_volume, 2))
            + " mL"
        ),

        Text(
            "Calculated acid concentration: "
            + str(round(calculated_concentration, 4))
            + " M"
        ),

        Text(
            "Actual randomized concentration: "
            + str(round(flask.concentration, 4))
            + " M"
        ),

        Text(
            "Equivalence volume: "
            + str(round(equivalence_volume(flask), 2))
            + " mL"
        ),

        Header("Titration Curve", 2),

        MatPlotLibPlot(),

        Text("The dashed vertical line represents the endpoint."),

        Button("Finish", "titration_complete")
    ])


@route
def titration_complete(state: State) -> Page:
    """Display the final thank-you page."""
    state.status = "complete"

    return Page(state, [
        Header("Titration Complete!"),

        Text(
            "Thank you for using the Virtual Titration Lab!"
        ),

        Text(
            "We hope this experiment helped you understand "
            "acid-base titrations."
        ),

        Button("Start Another Titration", "start_over"),

        Button("Review Calculations and Graph", "go_back")
    ])


@route
def start_over(state: State) -> Page:
    """Reset the experiment and return to the home page."""
    new_state = make_initial_state()

    return home(new_state)


@route
def go_back(state: State) -> Page:
    """Return to the calculations page."""
    return see_calculations(state)


if __name__ == "__main__":
    start_server(make_initial_state())
