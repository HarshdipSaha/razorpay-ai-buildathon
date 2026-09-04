from rebound.sim.clock import SimClock, RealClock
import time


def test_sim_clock_advances_on_demand():
    clock = SimClock(start=0.0)
    assert clock.now() == 0.0
    clock.advance(3600)
    assert clock.now() == 3600.0


def test_real_clock_uses_wall_time():
    clock = RealClock()
    t0 = clock.now()
    time.sleep(0.01)
    assert clock.now() > t0
