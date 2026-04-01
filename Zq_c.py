# -*- coding: utf-8 -*-
"""
Zero forcing (Z_q) -- pure-Python drop-in replacement for ``Zq_c.pyx``.

Provides the same public API as the Cython extension ``Zq_c.pyx`` without
requiring Cython compilation:

- :func:`push_zeros`
- :func:`push_zeros_looped`
- :func:`neighbors_connected_components`

All three functions accept the same argument types used by ``Zq.py``
(SageMath ``FrozenBitset`` / ``Bitset`` objects as well as plain Python
iterables) and return ``FrozenBitset`` objects when *return_bitset* is
``True``, matching the Cython extension's behaviour.

#######################################################################
#
# Copyright (C) 2011 Steve Butler, Jason Grout.
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

from sage.data_structures.bitset import FrozenBitset


def _to_set(bs):
    """Return a plain Python ``set`` from a bitset-like object or iterable."""
    return set(bs)


def _capacity(obj, neighbors):
    """Return the bitset capacity to use when constructing a return value."""
    try:
        return obj.capacity()
    except AttributeError:
        return len(neighbors)


def push_zeros(neighbors, subgraph, filled_set, return_bitset=True):
    """
    Run zero forcing as much as possible.

    :param neighbors: list of FrozenBitset -- the neighbors of each vertex
    :param subgraph: FrozenBitset -- the subgraph we are forcing on
    :param filled_set: FrozenBitset -- the initial filled vertices
    :param return_bitset: bool -- if ``True``, return the set of filled
        vertices after playing the game; if ``False``, return a boolean
        *can_push* which is ``True`` iff at least one force could happen.

    :returns: The returned filled set contains all of the initially filled
        vertices, even if they are outside of the subgraph.

    EXAMPLES::

        sage: from sage.data_structures.bitset import FrozenBitset
        sage: # Path graph P3: 0-1-2
        sage: n = 3
        sage: neighbors = [FrozenBitset([1], capacity=n),
        ....:               FrozenBitset([0, 2], capacity=n),
        ....:               FrozenBitset([1], capacity=n)]
        sage: subgraph = FrozenBitset(range(n), capacity=n)
        sage: filled = FrozenBitset([0], capacity=n)
        sage: result = push_zeros(neighbors, subgraph, filled)
        sage: set(result) == {0, 1, 2}
        True
        sage: push_zeros(neighbors, subgraph, filled, return_bitset=False)
        True
        sage: # No forcing possible when already fully filled
        sage: full = FrozenBitset(range(n), capacity=n)
        sage: push_zeros(neighbors, subgraph, full, return_bitset=False)
        False
    """
    capacity = _capacity(subgraph, neighbors)

    subgraph_set = _to_set(subgraph)
    filled = _to_set(filled_set)

    # unfilled = vertices in the subgraph that are not yet filled
    unfilled = subgraph_set - filled

    # filled_active = filled vertices that may still be able to force
    filled_active = set(filled)

    done = False
    while not done:
        done = True
        for n in list(filled_active):
            unfilled_nbrs = _to_set(neighbors[n]) & unfilled
            if not unfilled_nbrs:
                # n can never force anyone; retire it
                filled_active.discard(n)
            else:
                it = iter(unfilled_nbrs)
                new_filled = next(it)
                if next(it, None) is None:
                    # Exactly one unfilled neighbor: force it
                    filled_active.add(new_filled)
                    unfilled.discard(new_filled)
                    filled_active.discard(n)
                    if return_bitset:
                        done = False
                    else:
                        return True

    if return_bitset:
        result = (subgraph_set - unfilled) | filled
        return FrozenBitset(result, capacity=capacity)
    else:
        return False


def push_zeros_looped(neighbors, subgraph, filled_set, looped, unlooped,
                      return_bitset=True):
    """
    Run loop zero forcing as much as possible.

    Vertices that are not in *looped* or *unlooped* are undetermined, so the
    extra loop rules are not applied to those vertices.

    :param neighbors: list of FrozenBitset -- the neighbors of each vertex
    :param subgraph: FrozenBitset -- the subgraph we are forcing on
    :param filled_set: FrozenBitset -- the initial filled vertices
    :param looped: FrozenBitset -- the vertices that are looped
    :param unlooped: FrozenBitset -- the vertices that are not looped
    :param return_bitset: bool -- if ``True``, return the set of filled
        vertices after playing the game; if ``False``, return a boolean
        *can_push* which is ``True`` iff at least one force could happen.

    :returns: The returned filled set contains all of the initially filled
        vertices, even if they are outside of the subgraph.

    EXAMPLES::

        sage: from sage.data_structures.bitset import FrozenBitset
        sage: # Path graph P3: 0-1-2, all vertices unlooped
        sage: n = 3
        sage: neighbors = [FrozenBitset([1], capacity=n),
        ....:               FrozenBitset([0, 2], capacity=n),
        ....:               FrozenBitset([1], capacity=n)]
        sage: subgraph = FrozenBitset(range(n), capacity=n)
        sage: filled   = FrozenBitset([0], capacity=n)
        sage: looped   = FrozenBitset([], capacity=n)
        sage: unlooped = FrozenBitset(range(n), capacity=n)
        sage: result = push_zeros_looped(neighbors, subgraph, filled, looped, unlooped)
        sage: set(result) == {0, 1, 2}
        True
        sage: push_zeros_looped(neighbors, subgraph, filled, looped, unlooped,
        ....:                   return_bitset=False)
        True
    """
    capacity = _capacity(subgraph, neighbors)

    subgraph_set = _to_set(subgraph)
    filled = _to_set(filled_set)
    looped_set = _to_set(looped)
    unlooped_set = _to_set(unlooped)

    # unfilled = vertices in the subgraph that are not yet filled
    unfilled = subgraph_set - filled

    # active = filled vertices UNION unlooped vertices (both can force)
    active = filled | unlooped_set

    done = False
    while not done:
        done = True

        # Phase 1 – normal forcing from active vertices
        # Iterate over a snapshot of active (mirrors iterating active_copy
        # in the Cython code).
        for n in list(active):
            unfilled_nbrs = _to_set(neighbors[n]) & unfilled
            if not unfilled_nbrs:
                active.discard(n)
            else:
                it = iter(unfilled_nbrs)
                first_unfilled = next(it)
                if next(it, None) is None:
                    # Exactly one unfilled neighbor: force it
                    active.add(first_unfilled)
                    unfilled.discard(first_unfilled)
                    active.discard(n)
                    if not return_bitset:
                        return True
                    done = False

        # Phase 2 – die-alone rule for unfilled looped vertices
        # Corresponds to the else-clause of the Cython inner while loop,
        # which always executes when return_bitset=True (no break).
        # When return_bitset=False we would have already returned True above
        # if any Phase-1 force happened, so we only reach this when no
        # Phase-1 force was possible.
        for n in list(unfilled & looped_set):
            unfilled_nbrs = _to_set(neighbors[n]) & unfilled
            if not unfilled_nbrs:
                # n has no unfilled neighbours: it dies alone
                unfilled.discard(n)
                if not return_bitset:
                    return True
                done = False

    if return_bitset:
        result = (subgraph_set - unfilled) | filled
        return FrozenBitset(result, capacity=capacity)
    else:
        return False


def neighbors_connected_components(neighbors, subgraph):
    """
    Compute the connected components of the induced subgraph.

    :param neighbors: list of FrozenBitset -- the neighbors of each vertex
    :param subgraph: FrozenBitset -- the vertex set of the induced subgraph

    :returns: ``set`` of tuples; each tuple contains the sorted vertex
        indices of one connected component.

    EXAMPLES::

        sage: from sage.data_structures.bitset import FrozenBitset
        sage: # Two disjoint edges: 0-1 and 2-3
        sage: n = 4
        sage: neighbors = [FrozenBitset([1], capacity=n),
        ....:               FrozenBitset([0], capacity=n),
        ....:               FrozenBitset([3], capacity=n),
        ....:               FrozenBitset([2], capacity=n)]
        sage: subgraph = FrozenBitset(range(n), capacity=n)
        sage: cc = neighbors_connected_components(neighbors, subgraph)
        sage: cc == {(0, 1), (2, 3)}
        True
        sage: # Induced subgraph on vertices {1, 2, 3} gives one component
        sage: sub = FrozenBitset([1, 2, 3], capacity=n)
        sage: neighbors_connected_components(neighbors, sub) == {(2, 3)}
        True
    """
    subgraph_set = _to_set(subgraph)
    n = len(neighbors)

    # Restrict each vertex's neighbours to the subgraph once
    sub_neighbors = [_to_set(neighbors[i]) & subgraph_set for i in range(n)]

    components = set()
    seen = set()

    for i in range(n):
        if i in subgraph_set and i not in seen:
            # BFS from i
            component = set()
            queue = {i}
            while queue:
                visit = queue.pop()
                if visit not in component:
                    component.add(visit)
                    queue |= sub_neighbors[visit]

            components.add(tuple(sorted(component)))
            seen |= component

    return components
