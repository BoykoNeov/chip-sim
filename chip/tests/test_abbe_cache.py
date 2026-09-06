"""The memoized aerial image — a wall-clock optimization that must change NO number.

:func:`chip.litho.abbe_image` is a pure function of its arguments, and its consumers ask for the
*same* image many times over: the fab-line journey images one grating per line run and runs the line
103 times, so 6527 calls carry only 694 distinct argument sets. The whole image is therefore cached
on the exact arguments — bytes for the two arrays, so no float rounding enters the key — and the
result is copied out on every call.

Two things are asserted here, and they are the whole contract:

1. **Bit-identity.** A cached call returns exactly what the uncached body returns — ``array_equal``,
   not ``allclose``, on every argument axis the key carries (grid, orders, imaging, source, focus,
   aberrations, source-point count). The physics seams the litho tests pin (``z=0`` vs no defocus,
   ``Aberrations()`` vs ``None``) are bit-for-bit comparisons *between two abbe images*, so they only
   survive if the cache is exact — an approximate cache would silently loosen them.
2. **Isolation.** The array handed to a caller is a fresh copy of a read-only master. A consumer that
   normalizes its image in place (``litho.py`` §9 forms ``acid_dose·aerial/aerial.max()``; a demo may
   scale one for a plot) must not be able to reach the next caller's cache hit. This is the failure
   mode that would turn the speed-up into wrong numbers, and it is silent without this test.
"""
import numpy as np
import pytest

from chip import litho as L

IMG = L.Imaging(wavelength_nm=248.0, NA=0.6, sigma=0.6)
PITCH = 300.0
X = np.linspace(0.0, PITCH, 256, endpoint=False)
ORDERS = L.grating_orders(PITCH)


@pytest.fixture(autouse=True)
def _clean_cache():
    """Each test starts from an empty cache, so hit/miss counts are the test's own."""
    L.abbe_image.cache_clear()
    yield
    L.abbe_image.cache_clear()


def _uncached(x=X, orders=ORDERS, imaging=IMG, source_fs=None, n_source=21,
              defocus_nm=0.0, aberrations=None):
    """The body, called directly — the reference the cached path must reproduce exactly."""
    return L._abbe_uncached(np.asarray(x, dtype=float), orders, imaging, source_fs,
                            n_source, defocus_nm, aberrations)


# --------------------------------------------------------------------------- #
# 1. Bit-identity, on every axis the key carries
# --------------------------------------------------------------------------- #
CASES = {
    "plain": {},
    "defocus": {"defocus_nm": 120.0},
    "aberrations": {"aberrations": L.Aberrations(coma=0.05)},
    "explicit-source": {"source_fs": L.on_axis_source()},
    "n_source": {"n_source": 7},
    "coarse-pitch": {"orders": L.grating_orders(500.0, n_orders=9, duty=0.4)},
}


@pytest.mark.parametrize("name", list(CASES))
def test_cached_image_is_bit_identical_to_the_uncached_body(name):
    """A cached call equals the uncached computation exactly — array_equal, not allclose."""
    kw = CASES[name]
    assert np.array_equal(L.abbe_image(X, kw.get("orders", ORDERS), IMG,
                                       **{k: v for k, v in kw.items() if k != "orders"}),
                          _uncached(**kw))


@pytest.mark.parametrize("name", list(CASES))
def test_a_cache_hit_is_bit_identical_to_the_miss_that_filled_it(name):
    """The second (hit) call returns the same numbers as the first (miss) — the cache never drifts."""
    kw = CASES[name]
    orders = kw.get("orders", ORDERS)
    rest = {k: v for k, v in kw.items() if k != "orders"}
    first = L.abbe_image(X, orders, IMG, **rest)
    assert L.abbe_image.cache_info().misses == 1
    second = L.abbe_image(X, orders, IMG, **rest)
    assert L.abbe_image.cache_info().hits == 1
    assert np.array_equal(first, second)


def test_a_list_and_a_tuple_of_orders_hit_the_same_entry():
    """Orders are normalized into the key, so the caller's container type is not a cache axis."""
    first = L.abbe_image(X, list(ORDERS), IMG)
    second = L.abbe_image(X, tuple(ORDERS), IMG)
    info = L.abbe_image.cache_info()
    assert (info.hits, info.misses, info.currsize) == (1, 1, 1)   # not maxsize — that is tunable
    assert np.array_equal(first, second)


def test_a_scalar_source_point_and_its_one_element_array_agree():
    """``source_fs=0.0`` and ``np.array([0.0])`` are the same source, and give the same image.

    The key normalizes through ``atleast_1d``, so the two collapse onto one entry. That is only safe
    because the uncached body normalizes them identically too — asserted here against the body, so a
    future change to either normalization cannot silently make them share a wrong answer.
    """
    scalar = L.abbe_image(X, ORDERS, IMG, source_fs=0.0)
    array = L.abbe_image(X, ORDERS, IMG, source_fs=np.array([0.0]))
    assert np.array_equal(scalar, array)
    assert np.array_equal(scalar, _uncached(source_fs=0.0))
    assert np.array_equal(scalar, _uncached(source_fs=np.array([0.0])))


# --------------------------------------------------------------------------- #
# 2. Isolation — the failure mode that would make the speed-up wrong
# --------------------------------------------------------------------------- #
def test_mutating_a_returned_image_cannot_poison_a_later_hit():
    """A caller that scales/normalizes its image in place must not reach the cached master."""
    reference = _uncached()
    first = L.abbe_image(X, ORDERS, IMG)
    first *= 0.0                                    # the in-place normalize a consumer might do
    assert np.array_equal(L.abbe_image(X, ORDERS, IMG), reference)


def test_each_call_hands_back_a_distinct_writable_array():
    """Consumers get their own array — writable (they may normalize it) and not each other's."""
    a = L.abbe_image(X, ORDERS, IMG)
    b = L.abbe_image(X, ORDERS, IMG)
    assert a is not b
    assert a.flags.writeable and b.flags.writeable
    assert not np.shares_memory(a, b)


# --------------------------------------------------------------------------- #
# 3. The key discriminates — a different argument is a different image
# --------------------------------------------------------------------------- #
def test_every_argument_is_a_cache_axis():
    """Changing any keyed argument misses; none of them collapse onto another's entry."""
    calls = [
        dict(x=X, orders=ORDERS, imaging=IMG),
        dict(x=X + 1.0, orders=ORDERS, imaging=IMG),                       # a different grid
        dict(x=X, orders=L.grating_orders(400.0), imaging=IMG),            # a different mask
        dict(x=X, orders=ORDERS, imaging=L.Imaging(wavelength_nm=193.0, NA=0.6, sigma=0.6)),
        dict(x=X, orders=ORDERS, imaging=IMG, defocus_nm=90.0),
        dict(x=X, orders=ORDERS, imaging=IMG, n_source=9),
        dict(x=X, orders=ORDERS, imaging=IMG, aberrations=L.Aberrations(spherical=0.05)),
        dict(x=X, orders=ORDERS, imaging=IMG, source_fs=L.on_axis_source()),
    ]
    for c in calls:
        L.abbe_image(c.pop("x"), c.pop("orders"), c.pop("imaging"), **c)
    info = L.abbe_image.cache_info()
    assert (info.hits, info.misses) == (0, len(calls))


def test_the_degenerate_seams_still_hold_through_the_cache():
    """z=0 and Aberrations()-free are the *same* entry as the plain call — the v1.4/v1.10 seams."""
    plain = L.abbe_image(X, ORDERS, IMG)
    assert np.array_equal(L.abbe_image(X, ORDERS, IMG, defocus_nm=0.0), plain)
    assert np.array_equal(L.abbe_image(X, ORDERS, IMG, aberrations=None), plain)
    assert L.abbe_image.cache_info().misses == 1                 # all three are one computation
