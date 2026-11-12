from bakery import assert_equal

from main import (
    Flask, Titrant, State,
    make_initial_state,
    index,
    convert_volume_to_ml,
    convert_concentration_to_molarity,
    equivalence_volume,
    add_volume,
    calculate_ph,
    copy_flask,
    home,
    start_titration,
    equivalence_reached,
    continue_titrating,
    see_calculations,
    titration_complete,
    start_over,
    go_back
)


def test_unit_conversions():
    """Test volume and concentration conversions."""
    assert_equal(convert_volume_to_ml(0.5, "L"), 500)
    assert_equal(convert_volume_to_ml(25, "mL"), 25)

    assert_equal(
        convert_concentration_to_molarity(100, "mM"),
        0.1
    )

    assert_equal(
        convert_concentration_to_molarity(0.1, "M"),
        0.1
    )


def test_equivalence_volume():
    """Test the equivalence volume calculation."""
    flask = Flask(
        "HCl", 0.1, 25, False,
        Titrant("NaOH", 0.1, 0)
    )

    assert_equal(equivalence_volume(flask), 25)


def test_add_volume():
    """Test that titrant volumes accumulate correctly."""
    assert_equal(add_volume(2.5, 1.5), 4.0)
    assert_equal(add_volume(4.0, 2.0), 6.0)


def test_calculate_ph():
    """Test pH before, at, and after equivalence."""
    flask = Flask(
        "HCl", 0.1, 25, False,
        Titrant("NaOH", 0.1, 0)
    )

    assert_equal(round(calculate_ph(flask, 0), 2), 1.00)
    assert_equal(calculate_ph(flask, 25), 7.0)
    assert_equal(round(calculate_ph(flask, 30), 2), 11.96)


def test_copy_flask():
    """Test that snapshots preserve their original values."""
    flask = Flask(
        "HCl", 0.1, 25, False,
        Titrant("NaOH", 0.1, 3)
    )

    snapshot = copy_flask(flask)
    flask.titrant_added.volume_added = 8

    assert_equal(snapshot.titrant_added.volume_added, 3)


def test_home():
    """Test that the home page preserves its state."""
    state = make_initial_state()
    page = home(state)

    assert_equal(page.state, state)


def test_start_titration():
    """Test that starting creates a randomized experiment."""
    state = make_initial_state()

    page = start_titration(
        state, 25, "mL", "M", "HCl", "NaOH", 0.1
    )

    assert_equal(page.state.flask.volume, 25)
    assert_equal(page.state.flask.is_pink, False)

    assert_equal(
        page.state.flask.concentration >= 0.05,
        True
    )

    assert_equal(
        page.state.flask.concentration <= 0.20,
        True
    )


def test_equivalence_reached():
    """Test that the equivalence page preserves its state."""
    state = make_initial_state()
    page = equivalence_reached(state)

    assert_equal(page.state, state)


def test_continue_titrating():
    """Test that adding titrant reaches the endpoint."""
    flask = Flask(
        "HCl", 0.1, 25, False,
        Titrant("NaOH", 0.1, 24)
    )

    state = State(
        flask, [copy_flask(flask)],
        1, "mL", "M", "in_progress"
    )

    page = continue_titrating(state, 1)

    assert_equal(page.state.flask.is_pink, True)
    assert_equal(
        page.state.flask.titrant_added.volume_added,
        25
    )


def test_overshot_titration():
    """Test that adding titrant after equivalence overshoots."""
    flask = Flask(
        "HCl", 0.1, 25, True,
        Titrant("NaOH", 0.1, 25)
    )

    state = State(
        flask, [copy_flask(flask)],
        1, "mL", "M", "equivalence"
    )

    page = continue_titrating(state, 1)

    assert_equal(page.state.status, "overshot")
    assert_equal(
        page.state.flask.titrant_added.volume_added,
        26
    )


def test_see_calculations():
    """Test that the calculations page preserves the state."""
    state = make_initial_state()
    page = see_calculations(state)

    assert_equal(page.state, state)


def test_titration_complete():
    """Test that completing the experiment updates the status."""
    state = make_initial_state()
    page = titration_complete(state)

    assert_equal(page.state.status, "complete")


def test_start_over():
    """Test that starting over clears the experiment history."""
    state = make_initial_state()
    state.history.append(copy_flask(state.flask))

    page = start_over(state)

    assert_equal(page.state.history, [])
    assert_equal(page.state.status, "home")


def test_go_back():
    """Test that the back route returns to calculations."""
    state = make_initial_state()
    page = go_back(state)

    assert_equal(page.state, state)
    
def test_index():
    """Test that the index route displays the home page."""
    state = make_initial_state()
    page = index(state)

    assert_equal(page.state, state)
