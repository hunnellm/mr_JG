# -*- coding: utf-8 -*-
"""
Pure-Python implementation of the zero forcing wavefront algorithm.

This file re-implements the same algorithm as ``zero_forcing_wavefront.pyx``
using only standard Python/Sage constructs (no Cython, no compiled bitset C-API).
It can therefore be loaded directly from a URL in SageMath 10.7 via::

    load('https://raw.githubusercontent.com/hunnellm/mr_JG/master/zero_forcing_wavefront_py.py')

Why this file exists
--------------------
The original ``zero_forcing_wavefront.pyx`` uses Sage's internal Cython/C bitset
API (``sage.data_structures.bitset_base``, ``sage.data_structures.bitset``).
Those private internals changed across Sage versions, and a ``.pyx`` file cannot
be compiled on-the-fly from a raw HTTPS URL.  This pure-Python version sacrifices
some speed for universal loadability.

#######################################################################
#
# Copyright (C) 2009 Tracy Hall, Jason Grout, and Josh Lagrange.
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#######################################################################

EXAMPLES::

    sage: load('zero_forcing_wavefront_py.py')            # doctest: +SKIP
    sage: G = graphs.PetersenGraph()
    sage: result = zero_forcing_set_wavefront(G)
    sage: zf_number, zf_set, num_closures = result
    sage: zf_number == len(zf_set)
    True
    sage: isinstance(zf_set, list)
    True
    sage: isinstance(num_closures, int)
    True
"""


def _update_wavefront(neighbors, unfilled, n):
    """
    Run zero forcing propagation as much as possible (in place).

    A filled vertex that has exactly one unfilled neighbor forces that neighbor
    to become filled.  Repeat until no more forcing is possible.

    Parameters
    ----------
    neighbors : list of set
        ``neighbors[v]`` is the set of neighbors of vertex ``v``.
    unfilled : set
        Mutable set of currently unfilled vertices.  Modified in place.
    n : int
        Total number of vertices (0 .. n-1).
    """
    # All vertices that are not unfilled are "filled active"
    filled_active = set(range(n)) - unfilled

    done = False
    while not done:
        done = True
        for v in list(filled_active):
            unfilled_neighbors = neighbors[v] & unfilled
            if not unfilled_neighbors:
                # v has no unfilled neighbors; it can never force anyone
                filled_active.discard(v)
            else:
                # Check whether there is exactly one unfilled neighbor
                it = iter(unfilled_neighbors)
                new_filled = next(it)
                if next(it, None) is None:
                    # Exactly one unfilled neighbor: force it
                    filled_active.add(new_filled)
                    unfilled.discard(new_filled)
                    filled_active.discard(v)
                    done = False


def zero_forcing_set_wavefront(matrix):
    """
    Calculate a zero forcing set using the wavefront algorithm.

    INPUT:

    - ``matrix`` -- a Sage ``Graph`` or an adjacency matrix (any object
      supporting ``.nrows()`` and ``.nonzero_positions_in_row(i)``).

    OUTPUT:

    A 3-tuple ``(zero_forcing_number, zero_forcing_vertices, num_closures)``
    where

    - ``zero_forcing_number`` (int) is the size of the returned zero forcing set,
    - ``zero_forcing_vertices`` (list) is a zero forcing set, and
    - ``num_closures`` (int) is the number of closure entries stored during
      the search.

    EXAMPLES::

        sage: G = graphs.PetersenGraph()
        sage: zf_num, zf_set, closures = zero_forcing_set_wavefront(G)
        sage: zf_num == len(zf_set)
        True
        sage: zf_num
        5

        sage: # Works with an adjacency matrix too
        sage: M = graphs.PetersenGraph().adjacency_matrix()
        sage: zero_forcing_set_wavefront(M)[0]
        5
    """
    try:
        from sage.graphs.all import Graph
        if isinstance(matrix, Graph):
            matrix = matrix.adjacency_matrix()
    except ImportError:
        pass

    num_vertices = matrix.nrows()

    # Build neighbor sets once
    neighbors = [
        set(matrix.nonzero_positions_in_row(i)) for i in range(num_vertices)
    ]

    minimum_degree = min(len(neighbors[i]) for i in range(num_vertices))

    # closures maps frozenset(unfilled vertices) -> set(initial zf vertices)
    # Start: everything is unfilled, initial set is empty
    closures = {frozenset(range(num_vertices)): set()}

    for budget in range(minimum_degree, num_vertices + 1):
        for unfilled_frozen, initial_set in list(closures.items()):
            unfilled = set(unfilled_frozen)
            can_afford = budget - len(initial_set)

            for v in range(num_vertices):
                unfilled_neighbors = neighbors[v] & unfilled

                cost = max(1, len(unfilled_neighbors))
                if v not in unfilled:
                    cost -= 1
                    if cost == 0:
                        continue

                if cost <= can_afford:
                    new_initial = set(initial_set)

                    if v in unfilled:
                        new_initial.add(v)

                    # Pre-load unfilled neighbors into the initial set
                    # (they will be "filled" immediately in the first step)
                    new_initial |= unfilled_neighbors

                    new_unfilled = unfilled - new_initial

                    _update_wavefront(neighbors, new_unfilled, num_vertices)

                    # We got the smallest-index unfilled neighbor "for free"
                    # via zero forcing, so remove it from the initial set cost.
                    if unfilled_neighbors:
                        new_initial.discard(min(unfilled_neighbors))

                    if not new_unfilled:
                        # Found a zero forcing set that fills the whole graph
                        zero_forcing_vertices = list(new_initial)
                        return (
                            len(zero_forcing_vertices),
                            zero_forcing_vertices,
                            len(closures),
                        )

                    new_unfilled_frozen = frozenset(new_unfilled)
                    if new_unfilled_frozen not in closures:
                        closures[new_unfilled_frozen] = set(new_initial)

    # Should not be reached for a connected graph, but return a safe default.
    return num_vertices, list(range(num_vertices)), len(closures)
